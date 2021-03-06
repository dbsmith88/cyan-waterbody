import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import argparse
import time
from flaskr.db import p_set_geometry_tiles, set_geometry_tiles, save_data, get_waterbody_data, set_tile_bounds, set_index
from flaskr.aggregate import aggregate, retry_failed, p_aggregate
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cyan-waterbody")

parser = argparse.ArgumentParser(description="CyAN Waterbody data database management functions.")
parser.add_argument('--set_tiles', default=False, type=bool, help='Reset the geometry to tiles mapping.')
parser.add_argument('--set_tile_bounds', default=False, type=bool, help='Set the bounds for the raster tifs')
parser.add_argument('--get_data', default=False, type=bool, help='Get all data from the database for a specified OBJECTID')
parser.add_argument('--year', default=None, type=int, help="Year of data image to process.")
parser.add_argument('--day', default=None, type=int, help="Day of the year of the data image to process.")
parser.add_argument('--daily', default=True, type=bool, help="Process daily data image file.")
parser.add_argument('--weekly', default=False, type=bool, help="Process weekly data image file.")
parser.add_argument('--objectid', default=None, type=int, help="OBJECTID of a waterbody for a single waterbody aggregation")
parser.add_argument('--aggregate', default=False, type=bool, help='Save the aggregated data for the images in image_dir to the database.')
parser.add_argument('--retry', default=False, type=bool, help='Retry failed aggregation attempts')

PARALLEL = True


def async_aggregate(year: int, day: int, daily: bool):
    logger.info("Executing async waterbody aggregation for year: {}, day: {}, {}".format(year, day, "daily" if daily else "weekly"))
    t0 = time.time()
    try:
        completed = False
        offset = None
        while not completed:
            if PARALLEL:
                data, offset, completed = p_aggregate(year, day, daily, offset=offset)
            else:
                data, offset, completed = aggregate(year, day, daily, offset=offset)
            save_data(year, day, data=data, daily=daily)
        logger.info("Completed processing waterbody aggregation for year: {}, day: {}, {}".format(year, day, "daily" if daily else "weekly"))
    except Exception as e:
        logger.critical("ERROR processing data for waterbody aggregation. Message: {}".format(e))
    t1 = time.time()
    logger.info("Runtime: {} sec".format(round(t1 - t0, 4)))


def async_retry():
    retry_failed()
    retry_failed(daily=False)
    logger.info("Completed retry failed aggregations.")


if __name__ == "__main__":
    t0 = time.time()
    args = parser.parse_args()
    daily = args.daily if not args.weekly else False
    if args.set_tiles:
        if args.year is None or args.day is None:
            print("Mapping geometries to tiles requires reference tif, determined by year and day parameters.")
            exit()
        if PARALLEL:
            p_set_geometry_tiles(args.year, args.day, args.objectid)           # cpus=14 => 1:17:19
        else:
            set_geometry_tiles(args.year, args.day)
        logger.info("Completed setting waterbody to tile mapping.")
    elif args.aggregate:
        logger.info("Aggregating waterbodies for year: {}, day: {}, {}".format(args.year, args.day, "daily" if daily else "weekly"))
        completed = False
        offset = None
        while not completed:
            if PARALLEL:
                data, offset, completed = p_aggregate(args.year, args.day, daily=daily, offset=offset)
            else:
                data, offset, completed = aggregate(args.year, args.day, daily=daily, offset=offset)
            if data is None:
                logging.info("No images found for year: {}, day: {}, {}".format(args.year, args.day, "daily" if daily else "weekly"))
                exit()
            save_data(args.year, args.day, data=data, daily=daily)
        logger.info("Completed waterbody aggregation")
    elif args.get_data:
        data = get_waterbody_data(objectid=args.objectid, daily=daily)
        logger.info("Data: {}".format(data))
    elif args.retry:
        retry_failed()
        retry_failed(daily=False)
        logger.info("Completed retry failed aggregations.")
    elif args.set_tile_bounds:
        if args.year is None or args.day is None:
            print("Setting tile bounds requires reference tif, determined by year and day parameters.")
            exit()
        set_tile_bounds(int(args.year), int(args.day))
    else:
        print("")
        logger.info("Invalid input arguments\n")
        parser.print_help()
    t1 = time.time()
    print("")
    logger.info("Runtime: {} sec".format(round(t1 - t0, 4)))
