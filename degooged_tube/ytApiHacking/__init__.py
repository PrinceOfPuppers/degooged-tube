from .ytContIter import YtInitalPage
from . import controlPanel as ctrlp 
from .ytApiList import YtApiList
from .controlPanel import Upload, SearchType, SearchVideo, SearchChannel, ChannelInfo, VideoInfo, \
                          RelatedVideo, SearchElementFromData, Comment, ChannelPlaylist, PlaylistVideo, PlaylistInfo
from typing import Tuple, Union
from .helpers import addResultIfNotNone


# uploads
def uploadsOnExtend(res, **kwargs) -> list[Upload]:
    l = []
    for r in res:
        upload = Upload.fromData(r)
        if upload is not None:
            for key,item in kwargs.items():
                setattr(upload, key, item)
            l.append(upload)
    return l

def getUploadList(uploadsPage:YtInitalPage, onExtend = uploadsOnExtend, **kwargs) -> YtApiList[Upload]:
    '''kwargs are constant values to add to scraped data (ie channel name and url)'''
    return YtApiList(uploadsPage, ctrlp.uploadsApiUrl, ctrlp.uploadScrapeFmt, getInitalData=True, onExtend = onExtend, onExtendKwargs = kwargs)



# comments
def commentOnExtend(res):
    return [Comment.fromData(x) for x in res]

def getCommentList(videoPage: YtInitalPage, onExtend = commentOnExtend) -> YtApiList[str]:
    return YtApiList(videoPage, ctrlp.commentsApiUrl, ctrlp.commentScrapeFmt, onExtend = onExtend)




# video Info
def processVideoInfo(info):
    return VideoInfo.fromData(info)

def getVideoInfo(videoPage: YtInitalPage) -> Union[VideoInfo, None]:
    info = videoPage.scrapeInitalData(ctrlp.videoInfoScrapeFmt)
    return processVideoInfo(info)



# playlist Info
def processPlaylistInfo(info):
    return PlaylistInfo.fromData(info)

def getPlaylistInfo(playlistPage: YtInitalPage) -> Union[PlaylistInfo]:
    info = playlistPage.scrapeInitalData(ctrlp.playlistInfoScrapeFmt)
    return processPlaylistInfo(info)



# related videos
def relatedVideosOnExtend(res):
    l = []
    addResultIfNotNone(res, RelatedVideo.fromData, l)
    return l

def getRelatedVideoList(videoPage: YtInitalPage, onExtend = relatedVideosOnExtend):
    return YtApiList(videoPage, ctrlp.relatedVideosApiUrl, ctrlp.relatedVideosScrapeFmt, onExtend = onExtend)



# playlist videos
def playlistVideosOnExtend(res):
    l = []
    addResultIfNotNone(res, PlaylistVideo.fromData, l)
    return l

def getPlaylistVideoList(videoPage: YtInitalPage, onExtend = playlistVideosOnExtend):
    return YtApiList(videoPage, ctrlp.playlistVideosApiUrl, ctrlp.playlistVideosScrapeFmt, getInitalData = True, onExtend = onExtend)



# Channel Info
def getChannelInfoFromInitalPage(channelPage) -> ChannelInfo:
    data = channelPage.scrapeInitalData(ctrlp.channelInfoScrapeFmt)
    return ChannelInfo.fromData(data)

def getChannelInfo(channelUrl) -> ChannelInfo:
    channelUrl = sanitizeChannelUrl(channelUrl)
    channelPage = YtInitalPage.fromUrl(channelUrl)
    return getChannelInfoFromInitalPage(channelPage)



# Channel Playlists
def channelPlaylistsOnExtend(res, **kwargs) -> list[ChannelPlaylist]:
    l = []
    for r in res:
        channelPlaylist = ChannelPlaylist.fromData(r)
        if channelPlaylist is not None:
            for key,item in kwargs.items():
                setattr(channelPlaylist, key, item)
            l.append(channelPlaylist)
    return l

def getChannelPlaylistsList(channelPlaylistPage :YtInitalPage, onExtend = channelPlaylistsOnExtend, **kwargs) -> YtApiList[ChannelPlaylist]:
    '''kwargs are constant values to add to scraped data (ie channel name and url)'''
    return YtApiList(channelPlaylistPage, ctrlp.channelPlaylistsApiUrl,
                     ctrlp.channelPlaylistScrapeFmt, getInitalData=True, onExtend = onExtend, onExtendKwargs = kwargs)




# Search Filters
def processFilterData(res):
    l = []
    addResultIfNotNone(res, SearchType.fromData, l)
    return l

# Search Results
def searchOnExtend(res):
    l = []
    addResultIfNotNone(res, SearchElementFromData, l)
    return l

# Search
def getSearchList(term:str, onExtend = searchOnExtend) -> Tuple[YtApiList[Union[SearchVideo, SearchChannel]], list[SearchType]]:
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

