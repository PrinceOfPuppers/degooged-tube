import re
from .customExceptions import UnableToGetUploadTime, UnableToGetApproximateNum
import degooged_tube.config as cfg
from typing import Callable


def tryGet(data:dict, key: str, backupVal = ""):
    try:
        return data[key]
    except KeyError:
        #if cfg.testing:
        #    raise Exception(f"tryGet Missing Key {key}\nData:\n{data}")
        cfg.logger.debug(f"Missing Key {key} From Data, Returning BackupVal {backupVal}")
        return backupVal

def tryGetMultiKey(data:dict, backupVal, *args:str ):
    "varargs are keys"
    for key in args:
        try:
            return data[key]
        except KeyError:
            #if cfg.testing:
            #    raise Exception(f"tryGetMultiKey Missing Key {key}\nData:\n{data}")
            cfg.logger.debug(f"Missing Key {key} From Data, Trying Next Key")
            continue

    cfg.logger.debug(f"Returning BackupVal {backupVal} in tryGetMultiKey")
    return backupVal


def addResultIfNotNone(inputs:list, func:Callable, output:list):
    for input in inputs:
        d = func(input)
        if d is not None:
            output.append(d)

# Time Conversion

_ytTimeConversion = {
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

_timeDelineations = "|".join(_ytTimeConversion.keys())
_approxTimeRe = re.compile(r"(\d+)\s+("+_timeDelineations +r")\s+ago", re.I)

def approxTimeToUnix(currentTime:int, approxTime: str)->int:
    matches = _approxTimeRe.search(approxTime)
    if matches is None:
        raise UnableToGetUploadTime(f"Unrecognized Time String: {approxTime}")
    try:
        number = int(matches.group(1))
        delineation = matches.group(2)
    except:
        raise UnableToGetUploadTime(f"Error When Processing Time String: {approxTime}")

    return currentTime - number*_ytTimeConversion[delineation]


_ytNumConversion = {
    "k": int(1e3),
    "m": int(1e6),
    "b": int(1e9),
    "t": int(1e12),
    "q": int(1e15),
}

_numDelineations = "|".join(_ytNumConversion.keys())
_approxNumRe = re.compile(r"^(\d+)("+_numDelineations +r")?", re.I)

def getApproximateNum(approxNum: str)->int:
    sanitized = approxNum.strip().lower().replace(",", "")
    if sanitized[0] == 'n' and sanitized[1] == 'o':
        return 0
    matches = _approxNumRe.search(sanitized)
    if matches is None:
        raise UnableToGetApproximateNum(f"Unrecognized Number String: {approxNum}")
    try:
        number = int(matches.group(1))
    except:
        raise UnableToGetApproximateNum(f"Error When Processing Number String: {approxNum}")

    try:
        denominationText = matches.group(2)
        if denominationText is None:
            return number
    except IndexError:
        return number

    return number *_ytNumConversion[denominationText]



_videoIdRe = re.compile(r"(?:watch\?v=|youtu.be/)([a-zA-Z-0-9_-]+)", re.I)

def getVideoId(videoUrl: str) -> str:
    matches = _videoIdRe.search(videoUrl)
    if matches is None:
        return ''

    return matches.group(1)


def jsonRegex(*args, surroundingBrace = False):
    r = ""

    numPairs = len(args)//2
    for i in range(numPairs):
        r += r"\s*[\'\"]" + args[2*i] + r"[\'\"]\s*:\s*"
        r += r"[\'\"]" + args[2*i+1] + r"[\'\"]\s*.?"

    if surroundingBrace:
        r = "{" + r + "}"
    return r

