from degooged_tube.ytapiHacking.ytContIter import YtInitalPage
from degooged_tube.ytapiHacking.YtApiList import YtApiList

import degooged_tube.ytapiHacking.controlPanel as cp

import logging
import degooged_tube.config as cfg

def setupLogger():
    stream = logging.StreamHandler()
    cfg.logger.setLevel(logging.DEBUG)
    stream.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    cfg.logger.addHandler(stream)


def getUploadList(uploadsPage):
    if uploadsPage is None:
        raise Exception(f"Error Getting Uploads Page")

    return YtApiList(uploadsPage, cp.uploadsApiUrl, cp.uploadScrapeFmt, getInitalData=True, onExtend = cp.uploadsCallback)

def getCommentList(videoPage):
    if videoPage is None:
        raise Exception("Error Getting Page for video")

    return YtApiList(videoPage, cp.commentsApiUrl, cp.commentScrapeFmt, onExtend = cp.commentCallback)

def getRelatedVideoList(videoPage):
    return YtApiList(videoPage, cp.relatedVideosApiUrl, cp.relatedVideosScrapeFmt)


def cli():
    setupLogger()

    uploadsUrl = "https://www.youtube.com/c/karljobst/videos"
    uploadsPage = YtInitalPage.fromUrl(uploadsUrl)
    uploads = getUploadList(uploadsPage)

    upload = uploads[20]

    videoUrl = f"https://www.youtube.com/watch?v={upload['videoId']}"
    videoPage = YtInitalPage.fromUrl(videoUrl)
    if videoPage is None:
        raise Exception("Error Getting Page for video")

    relatedVideos = getRelatedVideoList(videoPage)
    print(relatedVideos[10])

    comments = getCommentList(videoPage)
    #print(comments[1])
    #print(comments[2])
    print(comments[10])




    #print(recommended[20])




