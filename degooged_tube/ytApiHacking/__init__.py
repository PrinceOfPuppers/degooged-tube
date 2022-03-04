from .ytContIter import YtInitalPage
from . import controlPanel as ctrlp 
from .ytApiList import YtApiList
#from urllib.parse import quote_plus
from .controlPanel import Upload, SearchType, SearchVideo, SearchChannel, ChannelInfo, VideoInfo, \
                          RelatedVideo, SearchElementFromData, Comment, ChannelPlaylist
from typing import Tuple, Union
from .helpers import addResultIfNotNone

# uploads
def uploadsCallback(res, **kwargs) -> list[Upload]:
    l = []
    for r in res:
        upload = Upload.fromData(r)
        if upload is not None:
            for key,item in kwargs.items():
                setattr(upload, key, item)
            l.append(upload)
    return l

def getUploadList(uploadsPage:YtInitalPage, onExtend = None, **kwargs) -> YtApiList[Upload]:
    '''kwargs are constant values to add to scraped data (ie channel name and url)'''
    if onExtend is None:
        callback = uploadsCallback
    else:
        callback = onExtend

    return YtApiList(uploadsPage, ctrlp.uploadsApiUrl, ctrlp.uploadScrapeFmt, getInitalData=True, onExtend = callback, onExtendKwargs = kwargs)



# comments
def commentCallback(res):
    return [Comment.fromData(x) for x in res]

def getCommentList(videoPage: YtInitalPage, onExtend = commentCallback) -> YtApiList[str]:
    return YtApiList(videoPage, ctrlp.commentsApiUrl, ctrlp.commentScrapeFmt, onExtend = onExtend)




# video Info
def processVideoInfo(info):
    return VideoInfo.fromData(info)

def getVideoInfo(videoPage: YtInitalPage) -> Union[VideoInfo, None]:
    info = videoPage.scrapeInitalData(ctrlp.videoInfoScrapeFmt)
    return processVideoInfo(info)



# related videos
def relatedVideosCallback(res):
    l = []
    addResultIfNotNone(res, RelatedVideo.fromData, l)
    return l

def getRelatedVideoList(videoPage: YtInitalPage, onExtend = relatedVideosCallback):
    return YtApiList(videoPage, ctrlp.relatedVideosApiUrl, ctrlp.relatedVideosScrapeFmt, onExtend = onExtend)




# Channel Info
def getChannelInfoFromInitalPage(channelPage) -> ChannelInfo:
    data = channelPage.scrapeInitalData(ctrlp.channelInfoScrapeFmt)
    return ChannelInfo.fromData(data)

def getChannelInfo(channelUrl) -> ChannelInfo:
    channelUrl = sanitizeChannelUrl(channelUrl)
    channelPage = YtInitalPage.fromUrl(channelUrl)
    return getChannelInfoFromInitalPage(channelPage)



# Channel Playlists
def channelPlaylistsCallback(res, **kwargs) -> list[ChannelPlaylist]:
    l = []
    for r in res:
        channelPlaylist = ChannelPlaylist.fromData(r)
        if channelPlaylist is not None:
            for key,item in kwargs.items():
                setattr(channelPlaylist, key, item)
            l.append(channelPlaylist)
    return l

def getChannelPlaylistsList(channelPlaylistPage :YtInitalPage, onExtend = None, **kwargs) -> YtApiList[ChannelPlaylist]:
    '''kwargs are constant values to add to scraped data (ie channel name and url)'''
    if onExtend is None:
        callback = channelPlaylistsCallback
    else:
        callback = onExtend

    return YtApiList(channelPlaylistPage, ctrlp.channelPlaylistsApiUrl,
                     ctrlp.channelPlaylistScrapeFmt, getInitalData=True, onExtend = callback, onExtendKwargs = kwargs)




# Search Filters
def processFilterData(res):
    l = []
    addResultIfNotNone(res, SearchType.fromData, l)
    return l

# Search Results
def searchCallback(res):
    l = []
    addResultIfNotNone(res, SearchElementFromData, l)
    return l


def getSearchList(term:str, onExtend = searchCallback) -> Tuple[YtApiList[Union[SearchVideo, SearchChannel]], list[SearchType]]:
    url = ctrlp.searchUrl + term

    searchInitalPage = YtInitalPage.fromUrl(url)
    searchList = YtApiList(searchInitalPage, ctrlp.searchApiUrl, ctrlp.searchScrapeFmt, getInitalData = True, onExtend = onExtend)
    filterData = processFilterData( searchInitalPage.scrapeInitalData(ctrlp.searchFilterScrapeFmt) )
    return searchList, filterData


def sanitizeChannelUrl(channelUrl: str, path:str = ''):
    channelUrl = channelUrl.strip(' ')

    for splitStr in ctrlp.channelUrlSanitizationSplitsPostfix:
        channelUrl = channelUrl.split(splitStr,1)[0]

    for splitStr in ctrlp.channelUrlSanitizationSplitsPrefix:
        channelUrl = channelUrl.split(splitStr,1)[-1]

    return "https" + channelUrl + path

