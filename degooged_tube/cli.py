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


def cli():
    setupLogger()

    uploadUrl = "https://www.youtube.com/c/karljobst/videos"
    uploadsPage = YtInitalPage.fromUrl(uploadUrl, getDataInScript = True)

    if uploadsPage is None:
        raise Exception("No Uploads Page")

    uploads = YtApiList(uploadsPage, cp.uploadsApiUrl, cp.uploadScrapeFmt, getInitalData=True, onExtend = cp.uploadsCallback)

    upload = uploads[20]
    # print(f"Getting Commments for Upload: {upload['title']}")

    videoUrl = f"https://www.youtube.com/watch?v={upload['videoId']}"

    videoPage = YtInitalPage.fromUrl(videoUrl, getDataInScript = True)
    if videoPage is None:
        raise Exception("Error Getting Page for video")

    print(videoPage.apiUrls)

    comments = YtApiList(videoPage, cp.commentsApiUrl, cp.commentScrapeFmt, onExtend = cp.commentCallback)
    print(comments[1])
    print('\n')
    print(comments[2])
    print('\n')
    print(comments[3])
    print('\n')
    print(comments[4])
    print('\n')
    print(comments[40])

