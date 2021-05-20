import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from flask import Flask, request
from flaskr.db import get_waterbody_data, get_waterbody_bypoint, get_waterbody
from flaskr.geometry import get_waterbody_byname, get_waterbody_properties
from main import async_aggregate, async_retry
import threading
import logging
import json

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("cyan-waterbody")
logger.info("CyAN Waterbody Flask App")


@app.route('/')
def status_check():
    return "42", 200


@app.route('/waterbody/data/')
def get_data():
    args = request.args
    if "OBJECTID" in args:
        objectid = args["OBJECTID"]
    else:
        return "Missing required waterbody objectid parameter 'OBJECTID'", 200
    start_year = None
    if "start_year" in args:
        start_year = int(args["start_year"])
    start_day = None
    if "start_day" in args:
        start_day = int(args["start_day"])
    end_year = None
    if "end_year" in args:
        end_year = int(args["end_year"])
    end_day = None
    if "end_day" in args:
        end_day = int(args["end_day"])
    daily = True
    if "daily" in args:
        daily = (args["daily"] == "True")
    ranges = None
    if "ranges" in args:
        try:
            ranges = json.loads(args["ranges"])
        except Exception as e:
            logger.info("Unable to load provided ranges object, error: {}".format(e))
    geojson = None
    if "geojson" in args:
        try:
            geojson = json.loads(args["geojson"])
        except Exception as e:
            message = "Unable to load provided geojson, error: {}".format(e)
            logger.info(message)
            return message, 200
    # if geojson is not None:
    #     data = get_custom_waterbody_data(geojson=geojson, daily=daily, start_year=start_year, start_day=start_day,
    #                                      end_year=end_year, end_day=end_day, ranges=ranges)
    data = get_waterbody_data(objectid=objectid, daily=daily, start_year=start_year, start_day=start_day,
                                  end_year=end_year, end_day=end_day, ranges=ranges)
    results = {"OBJECTID": objectid, "daily": daily, "data": data}
    return results, 200


@app.route('/waterbody/search/')
def get_objectid():
    args = request.args
    lat = None
    lng = None
    gnis = None
    if "lat" in args:
        lat = float(args["lat"])
    if "lng" in args:
        lng = float(args["lng"])
    if "name" in args:
        gnis = str(args["name"])
    error = []
    if lat is None:
        error.append("Missing required latitude parameter 'lat'")
    if lng is None:
        error.append("Missing required longitude parameter 'lng'")
    if gnis is not None:
        error = []
    if len(error) > 0:
        return ", ".join(error), 200
    if gnis is not None:
        data = get_waterbody_byname(gnis_name=gnis)
        results = {"waterbodies": data if len(data) > 0 else "NA"}
    else:
        objectid, gnis = get_waterbody_bypoint(lat=lat, lng=lng)
        if objectid is not None and gnis is not None:
            data = get_waterbody_byname(gnis)
            results = {"lat": lat, "lng": lng,
                       "waterbodies": data if len(data) > 0 else "NA"}
        else:
            results = {"lat": lat, "lng": lng, "OBJECTID": int(objectid) if objectid is not None else "NA"}
    return results, 200


@app.route('/waterbody/properties/')
def get_properties():
    args = request.args
    objectid = None
    if "OBJECTID" in args:
        objectid = int(args["OBJECTID"])
    elif "objectid" in args:
        objectid = int(args["objectid"])
    else:
        return "Missing required waterbody objectid parameter 'OBJECTID'", 200
    data = get_waterbody_properties(objectid=objectid)
    result = {"objectid": objectid, "properties": data}
    return result, 200


@app.route('/waterbody/geometry/')
def get_geometry():
    args = request.args
    objectid = None
    if "OBJECTID" in args:
        objectid = int(args["OBJECTID"])
    elif "objectid" in args:
        objectid = int(args["objectid"])
    else:
        return "Missing required waterbody objectid parameter 'OBJECTID'", 200
    data = get_waterbody(objectid=objectid)
    results = {"objectid": objectid, "geojson": data}
    return results, 200


@app.route('/waterbody/aggregate/')
def aggregate():
    args = request.args
    year = None
    day = None
    daily = True
    if "year" in args:
        year = int(args["year"])
    if "day" in args:
        day = int(args["day"])
    if "daily" in args:
        daily = (args["daily"] == "True")
    error = []
    if year is None:
        error.append("Missing required year parameter 'year'")
    if day is None:
        error.append("Missing required day parameter 'day'")
    if len(error) > 0:
        return ", ".join(error), 200
    th = threading.Thread(target=async_aggregate, args=(year, day, daily))
    th.start()
    return "Waterbody aggregation initiated for year: {}, day: {}, {}".format(year, day, "daily" if daily else "weekly"), 200


@app.route('/waterbody/aggregate/retry/')
def aggregate_retry():
    th = threading.Thread(target=async_retry)
    th.start()
    return "Initiated retry for dialy and weekly aggregations...", 200


if __name__ == "__main__":
    logging.info("Starting up CyAN waterbody flask app")
    app.run(debug=True, host='0.0.0.0', port=8080)
