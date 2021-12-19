from .ytContIter import YtInitalPage
from . import controlPanel as ctrlp 
from .ytApiList import YtApiList
#from urllib.parse import quote_plus
from .controlPanel import Upload, SearchType, SearchVideo, SearchChannel, ChannelInfo, SearchFilter, VideoInfo, RelatedVideo
from typing import Tuple


# uploads
def uploadsCallback(res) -> list[Upload]:
    return [Upload.fromData(x) for x in res]

def getUploadList(uploadsPage:YtInitalPage, onExtend = uploadsCallback) -> YtApiList[Upload]:
    return YtApiList(uploadsPage, ctrlp.uploadsApiUrl, ctrlp.uploadScrapeFmt, getInitalData=True, onExtend = onExtend)



# comments
def commentCallback(res):
    for i,comment in enumerate(res):
        res[i] = ''.join(comment)

    return res

def getCommentList(videoPage: YtInitalPage, onExtend = commentCallback) -> YtApiList[str]:
    return YtApiList(videoPage, ctrlp.commentsApiUrl, ctrlp.commentScrapeFmt, onExtend = onExtend)




# video Info
def processVideoInfo(info):
    # Todo join description
    return VideoInfo.fromData(info)

def getVideoInfo(videoPage: YtInitalPage) -> VideoInfo:
    info = videoPage.scrapeInitalData(ctrlp.videoInfoScrapeFmt)
    return processVideoInfo(info)



# related videos
def relatedVideosCallback(res):
    return [RelatedVideo.fromData(x) for x in res]

def getRelatedVideoList(videoPage: YtInitalPage, onExtend = relatedVideosCallback):
    return YtApiList(videoPage, ctrlp.relatedVideosApiUrl, ctrlp.relatedVideosScrapeFmt, onExtend = onExtend)




# Channel Info
def getChannelInfoFromInitalPage(channelPage) -> ChannelInfo:
    data = channelPage.scrapeInitalData(ctrlp.channelInfoScrapeFmt)

    if len(data) != 2:
        raise Exception("Update GetChannelInfoFromInitalPage")

    resultIndex = 0 if list(data[0].keys())[0] != 'metadata' else 1

    result = data[resultIndex]
    metadata = data[(resultIndex+1)%2]['metadata']

    result['channelUrl'] = sanitizeChannelUrl(metadata['channelUrl'])
    result['description'] = metadata['description']

    return ChannelInfo.fromData(result)

def getChannelInfo(channelUrl) -> ChannelInfo:
    channelUrl = sanitizeChannelUrl(channelUrl)
    channelPage = YtInitalPage.fromUrl(channelUrl)
    return getChannelInfoFromInitalPage(channelPage)




# Search Filters
def processFilterData(res):
    return [SearchType.fromData(r) for r in res]


# Search results
def searchVideoCallback(res):
    l = []
    for r in res:
        x = SearchVideo.fromData(r)
        if x is not None:
            l.append(x)
    return l

def searchChannelCallback(res) -> list[SearchChannel]:
    l = []
    for r in res:
        x = SearchChannel.fromData(r)
        if x is not None:
            l.append(x)
    return l

def getSearchVideoList(term:str) -> Tuple[YtApiList[SearchVideo], list[SearchType]]:
    url = ctrlp.searchUrl + term

    searchInitalPage = YtInitalPage.fromUrl(url)
    searchList = YtApiList(searchInitalPage, ctrlp.searchApiUrl, ctrlp.searchVideoScrapeFmt, getInitalData = True, onExtend = searchVideoCallback)
    filterData = processFilterData( searchInitalPage.scrapeInitalData(ctrlp.searchFilterScrapeFmt) )
    return searchList, filterData

def getSearchChannelList(term:str) -> Tuple[YtApiList[SearchChannel], list[SearchType]]:
    url = ctrlp.searchUrl + term

    searchInitalPage = YtInitalPage.fromUrl(url)
    searchList = YtApiList(searchInitalPage, ctrlp.searchApiUrl, ctrlp.searchChannelScrapeFmt, getInitalData = True, onExtend = searchChannelCallback)
    filterData = processFilterData( searchInitalPage.scrapeInitalData(ctrlp.searchFilterScrapeFmt) )
    return searchList, filterData


def sanitizeChannelUrl(channelUrl: str, path:str = ''):
    channelUrl = channelUrl.strip(' ')

    for splitStr in ctrlp.channelUrlSanitizationSplitsPostfix:
        channelUrl = channelUrl.split(splitStr,1)[0]

    for splitStr in ctrlp.channelUrlSanitizationSplitsPrefix:
        channelUrl = channelUrl.split(splitStr,1)[-1]

    return "https" + channelUrl + path

