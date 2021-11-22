from .ytContIter import YtInitalPage
from . import controlPanel as ctrlp 
from .ytApiList import YtApiList
from .customExceptions import UnableToGetUploadTime
from urllib.parse import quote_plus
import time

currentTime = int(time.time())



# uploads
def uploadsCallback(res):
    for r in res:
        r['unixTime'] = approxTimeToUnix(currentTime, r['uploadedOn'])
    return res

def getUploadList(uploadsPage, onExtend = uploadsCallback):
    return YtApiList(uploadsPage, ctrlp.uploadsApiUrl, ctrlp.uploadScrapeFmt, getInitalData=True, onExtend = onExtend)




# comments
def commentCallback(res):
    for i,comment in enumerate(res):
        res[i] = ''.join(comment)

    return res

def getCommentList(videoPage: YtInitalPage, onExtend = commentCallback):
    return YtApiList(videoPage, ctrlp.commentsApiUrl, ctrlp.commentScrapeFmt, onExtend = onExtend)




# video Info
def processVideoInfo(info):
    # Todo join description
    return info

def getVideoInfo(videoPage: YtInitalPage):
    info = videoPage.scrapeInitalData(ctrlp.videoInfoScrapeFmt)
    return processVideoInfo(info)



# related videos
def getRelatedVideoList(videoPage):
    return YtApiList(videoPage, ctrlp.relatedVideosApiUrl, ctrlp.relatedVideosScrapeFmt)



# Channel Info
def getChannelInfoFromInitalPage(channelPage):
    data = channelPage.scrapeInitalData(ctrlp.channelInfoScrapeFmt)

    if len(data) != 2:
        raise Exception("Update GetChannelInfoFromInitalPage")

    resultIndex = 0 if list(data[0].keys())[0] != 'metadata' else 1

    result = data[resultIndex]
    metadata = data[(resultIndex+1)%2]['metadata']

    result['channelUrl'] = sanitizeChannelUrl(metadata['channelUrl'])
    result['description'] = metadata['description']

    return result

def getChannelInfo(channelUrl):
    channelUrl = sanitizeChannelUrl(channelUrl)
    channelPage = YtInitalPage.fromUrl(channelUrl)
    return getChannelInfoFromInitalPage(channelPage)



# Search
def searchCallback(res):
    return res

def getSearchList(term, onExtend = searchCallback):
    url = ctrlp.searchUrl + quote_plus(term)
    searchInitalPage = YtInitalPage.fromUrl(url)
    return YtApiList(searchInitalPage, ctrlp.searchApiUrl, ctrlp.searchScrapeFmt, getInitalData = True, onExtend = onExtend)



def sanitizeChannelUrl(channelUrl: str, path:str = ''):
    channelUrl = channelUrl.strip(' ')

    for splitStr in ctrlp.channelUrlSanitizationSplitsPostfix:
        channelUrl = channelUrl.split(splitStr,1)[0]

    for splitStr in ctrlp.channelUrlSanitizationSplitsPrefix:
        channelUrl = channelUrl.split(splitStr,1)[-1]

    return "https" + channelUrl + path

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
