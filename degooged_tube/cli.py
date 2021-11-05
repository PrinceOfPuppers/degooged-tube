import degooged_tube.ytApiHacking as ytapih
import logging
import degooged_tube.config as cfg

def setupLogger():
    stream = logging.StreamHandler()
    cfg.logger.setLevel(logging.DEBUG)
    stream.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    cfg.logger.addHandler(stream)


# def getCombinedUploads(uploadLists: list[YtApiList], limit: int, offset: int, prevOrdering:list[str] = None):

def cli():
    setupLogger()
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

