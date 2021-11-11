import sys
import degooged_tube.ytApiHacking as ytapih
import logging
import degooged_tube.config as cfg
import json

def setupLogger():
    stream = logging.StreamHandler(sys.stdout)
    cfg.logger.setLevel(logging.DEBUG)
    stream.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    cfg.logger.addHandler(stream)


def exampleCode1():
    channelData = ytapih.getChannelInfo('https://www.youtube.com/c/MattMcMuscles')
    uploadsUrl = 'https://www.youtube.com' + channelData['baseUrl'] + '/videos'

    uploadsPage = ytapih.YtInitalPage.fromUrl(uploadsUrl)
    uploads = ytapih.getUploadList(uploadsPage)

    upload = uploads[20]

    videoUrl = f"https://www.youtube.com/watch?v={upload['videoId']}"
    videoPage = ytapih.YtInitalPage.fromUrl(videoUrl)
    if videoPage is None:
        raise Exception("Error Getting Page for video")

    relatedVideos = ytapih.getRelatedVideoList(videoPage)
    print(relatedVideos[10])

    comments = ytapih.getCommentList(videoPage)
    print(comments[10])


def cli():
    setupLogger()
    videoPage = ytapih.YtInitalPage.fromUrl("https://www.youtube.com/watch?v=AFrQ1_2bbsI")
    print(ytapih.getVideoInfo(videoPage))
    #related = ytapih.getRelatedVideoList(vid)
    #print(related[0])
    print(json.dumps(videoPage.initalData, indent=2))
