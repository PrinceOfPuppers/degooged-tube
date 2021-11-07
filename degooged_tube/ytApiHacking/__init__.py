from .ytContIter import YtInitalPage
from . import controlPanel as ctrlp 
from .ytApiList import YtApiList
from .customExceptions import UnableToGetUploadTime
import time

currentTime = int(time.time())

def uploadsCallback(res):
    for r in res:
        r['unixTime'] = approxTimeToUnix(currentTime, r['uploaded on'])
    return res

def getUploadList(uploadsPage):
    return YtApiList(uploadsPage, ctrlp.uploadsApiUrl, ctrlp.uploadScrapeFmt, getInitalData=True, onExtend = uploadsCallback)



def commentCallback(res):
    for i,comment in enumerate(res):
        res[i] = ''.join(comment)

    return res

def getCommentList(videoPage):
    return YtApiList(videoPage, ctrlp.commentsApiUrl, ctrlp.commentScrapeFmt, onExtend = commentCallback)



def getRelatedVideoList(videoPage):
    return YtApiList(videoPage, ctrlp.relatedVideosApiUrl, ctrlp.relatedVideosScrapeFmt)

def getChannelInfo(channelUrl: str):
    channelUrl = sanitizeChannelUrl(channelUrl)
    channelPage = YtInitalPage.fromUrl(channelUrl)
    data = channelPage.scrapeInitalData(ctrlp.channelInfoScrapeFmt)
    assert type(data) is dict
    return data

def sanitizeChannelUrl(channelUrl: str, path:str = ''):
    channelUrl = channelUrl.strip(' ')

    for splitStr in ctrlp.channelUrlSanitizationSplits:
        channelUrl = channelUrl.split(splitStr,1)[0]

    return channelUrl + path

def approxTimeToUnix(currentTime:int, approxTime: str)->int:
    matches = ctrlp.approxTimeRe.search(approxTime)
    if matches is None:
        raise UnableToGetUploadTime(f"Unrecognized Time String: {approxTime}")
    try:
        number = int(matches.group(1))
        delineation = matches.group(2)
    except:
        raise UnableToGetUploadTime(f"Error When Processing Time String: {approxTime}")

    return currentTime - number*ctrlp.ytTimeConversion[delineation]
