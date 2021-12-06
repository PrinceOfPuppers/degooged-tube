import re
from .customExceptions import UnableToGetUploadTime


def tryGet(data:dict, key: str, backupVal = ""):
    try:
        return data[key]
    except KeyError:
        return backupVal

# Time Conversion

ytTimeConversion = {
    "second":  1,
    "seconds": 1,

    "minute":  60,
    "minutes": 60,

    "hour":    3600,
    "hours":   3600,

    "day":     86400,
    "days":    86400,

    "week":    604800,
    "weeks":   604800,

    "month":   2419200,
    "months":  2419200,

    "year":    29030400,
    "years":   29030400,
}

timeDelineations = "|".join(ytTimeConversion.keys())
approxTimeRe = re.compile(r"(\d+)\s+("+timeDelineations +r")\s+ago", re.I)

def approxTimeToUnix(currentTime:int, approxTime: str)->int:
    matches = approxTimeRe.search(approxTime)
    if matches is None:
        raise UnableToGetUploadTime(f"Unrecognized Time String: {approxTime}")
    try:
        number = int(matches.group(1))
        delineation = matches.group(2)
    except:
        raise UnableToGetUploadTime(f"Error When Processing Time String: {approxTime}")

    return currentTime - number*ytTimeConversion[delineation]

