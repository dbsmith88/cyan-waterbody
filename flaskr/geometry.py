import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import fiona
import os

WATERBODY_DBF = os.path.join(os.getenv("WATERBODY_DBF", "D:\\data\cyan_rare\\mounts\\geometry"), "waterbodies_2.dbf")


def get_waterbody(objectid: int = None, objectids: list = None):
    features = []
    with fiona.open(WATERBODY_DBF) as waterbodies:
        crs = waterbodies.crs
        for f in waterbodies:
            if objectid:
                if objectid == f["properties"]["OBJECTID"]:
                    features.append(f)
                    continue
            elif objectids:
                if f["properties"]["OBJECTID"] in objectids:
                    features.append(f)
                    continue
            else:
                features.append(f)
    return features, crs


def get_waterbody_byname(gnis_name: str):
    gnis_name = gnis_name.replace('\'', "").replace('\"', "")
    waterbody = []
    with fiona.open(WATERBODY_DBF) as waterbodies:
        for f in waterbodies:
            if gnis_name.lower() in f["properties"]["GNIS_NAME"].lower():
                wb = {"name": f["properties"]["GNIS_NAME"], "objectid": int(f["properties"]["OBJECTID"])}
                waterbody.append(wb)
    return waterbody


def get_waterbody_properties(objectid: int):
    metadata = {}
    with fiona.open(WATERBODY_DBF) as waterbodies:
        for f in waterbodies:
            if objectid == int(f["properties"]["OBJECTID"]):
                metadata = f["properties"]
                break
    return metadata
