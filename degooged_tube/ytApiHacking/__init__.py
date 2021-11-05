from .ytContIter import YtInitalPage
from . import controlPanel as ctrlp 
from .ytApiList import YtApiList

def getUploadList(uploadsPage):
    return YtApiList(uploadsPage, ctrlp.uploadsApiUrl, ctrlp.uploadScrapeFmt, getInitalData=True, onExtend = ctrlp.uploadsCallback)

def getCommentList(videoPage):
    return YtApiList(videoPage, ctrlp.commentsApiUrl, ctrlp.commentScrapeFmt, onExtend = ctrlp.commentCallback)

def getRelatedVideoList(videoPage):
    return YtApiList(videoPage, ctrlp.relatedVideosApiUrl, ctrlp.relatedVideosScrapeFmt)

def getChannelInfo(channelUrl: str):
    channelUrl = sanitizeChannelUrl(channelUrl)
    channelPage = YtInitalPage.fromUrl(channelUrl)
    data = channelPage.scrapeInitalData(ctrlp.channelInfoScrapeFmt)
    assert type(data) is dict
    return data

def sanitizeChannelUrl(channelUrl: str):
    channelUrl = channelUrl.strip(' ')

    for splitStr in ctrlp.channelUrlSanitizationSplits:
        channelUrl = channelUrl.split(splitStr,1)[0]

    return channelUrl
