from .ytContIter import YtInitalPage
from . import controlPanel as ctrlp 
from .ytApiList import YtApiList
from .customExceptions import UnableToGetUploadTime
import time

currentTime = int(time.time())


# uploads
class Upload:
    def __init__(self, data:dict):
        self.videoId:str            = data['videoId']
        self.url:str                = 'https://www.youtube.com/watch?v=' + data['videoId']
        self.unixTime:int           = approxTimeToUnix(currentTime, data['uploadedOn'])
        self.thumbnails:dict        = data['thumbnails']
        self.uploadedOn:str         = data['uploadedOn']
        self.views:str              = data['views']
        self.duration:str           = data['duration']
        self.title:str              = data['title']

        # the following are added by subbox
        self.channelName:str = ''
        self.channelUrl:str = ''
    
    def __repr__(self):
        return f'{self.title}\n     > {self.channelName} - {self.views}'

    def __str__(self):
        return self.__repr__()

def uploadsCallback(res) -> list[Upload]:
    return [Upload(x) for x in res]

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
class ChannelInfo:
    def __init__(self, data:dict):
        self.channelName:str        = data['channelName']
        self.avatar:list            = data['avatar']
        self.banners:list           = data['banners']
        self.mobileBanners:list     = data['mobileBanners']
        self.subscribers:str        = data['subscribers']
        self.channelUrl:str         = data['channelUrl']
        self.description:str        = data['description']

def getChannelInfoFromInitalPage(channelPage) -> ChannelInfo:
    data = channelPage.scrapeInitalData(ctrlp.channelInfoScrapeFmt)

    if len(data) != 2:
        raise Exception("Update GetChannelInfoFromInitalPage")

    resultIndex = 0 if list(data[0].keys())[0] != 'metadata' else 1

    result = data[resultIndex]
    metadata = data[(resultIndex+1)%2]['metadata']

    result['channelUrl'] = sanitizeChannelUrl(metadata['channelUrl'])
    result['description'] = metadata['description']

    return ChannelInfo(result)

def getChannelInfo(channelUrl) -> ChannelInfo:
    channelUrl = sanitizeChannelUrl(channelUrl)
    channelPage = YtInitalPage.fromUrl(channelUrl)
    return getChannelInfoFromInitalPage(channelPage)




# Search
def searchCallback(res):
    return res

def processFilterData(res):
    result = {}

    for filterSet in res:
        x = {}
        searchType = filterSet['searchType']
        filters = filterSet['filters']
        for filter in filters:

            try:
                label = filter['label']
                searchUrlFragment = filter['searchUrlFragment']
            except KeyError:
                continue

            x[label] = searchUrlFragment
        result[searchType] = x

    return result

def getSearchList(term, onExtend = searchCallback, processData = processFilterData):
    url = ctrlp.searchUrl + term
    searchInitalPage = YtInitalPage.fromUrl(url)
    searchList = YtApiList(searchInitalPage, ctrlp.searchApiUrl, ctrlp.searchScrapeFmt, getInitalData = True, onExtend = onExtend)
    filterData = processData( searchInitalPage.scrapeInitalData(ctrlp.searchFilterScraper) )
    return searchList, filterData


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
