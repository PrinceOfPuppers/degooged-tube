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

def getUploadList(uploadsPage, onExtend = uploadsCallback):
    return YtApiList(uploadsPage, ctrlp.uploadsApiUrl, ctrlp.uploadScrapeFmt, getInitalData=True, onExtend = onExtend)


def commentCallback(res):
    for i,comment in enumerate(res):
        res[i] = ''.join(comment)

    return res

def getCommentList(videoPage: YtInitalPage, onExtend = commentCallback):
    return YtApiList(videoPage, ctrlp.commentsApiUrl, ctrlp.commentScrapeFmt, onExtend = onExtend)



def processVideoInfo(info):
    # Todo join description
    return info

def getVideoInfo(videoPage: YtInitalPage):
    info = videoPage.scrapeInitalData(ctrlp.videoInfoScrapeFmt)
    return processVideoInfo(info)




def getRelatedVideoList(videoPage):
    return YtApiList(videoPage, ctrlp.relatedVideosApiUrl, ctrlp.relatedVideosScrapeFmt)

def getChannelInfo(channelUrl: str):
    channelUrl = sanitizeChannelUrl(channelUrl)
    channelPage = YtInitalPage.fromUrl(channelUrl)
    data = channelPage.scrapeInitalData(ctrlp.channelInfoScrapeFmt)
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

