import degooged_tube.ytApiHacking as ytapih
import logging
import degooged_tube.config as cfg
from dataclasses import dataclass
from degooged_tube.subbox import SubBox

def setupLogger():
    stream = logging.StreamHandler()
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
    subscribed = ['https://www.youtube.com/c/MattMcMuscles', 'https://www.youtube.com/channel/UC3ltptWa0xfrDweghW94Acg']
    channelUrlGenerator = ( ytapih.sanitizeChannelUrl(url) + '/videos' for url in subscribed )
    subBox = SubBox.fromUrls(channelUrlGenerator)

    uploads1 = subBox.getPaginatedUploads(1, 10)

    videoIds1 = [upload['videoId'] for upload in uploads1]

    uploads2 = subBox.getPaginatedUploads(2, 10)
    videoIds2 = [upload['videoId'] for upload in uploads2]

    intersection = list( set(videoIds1)&set(videoIds2) )
    if len(intersection) != 0:
        print(videoIds1)
        print(videoIds2)
        print(intersection)
        raise Exception()


    #print(json.dumps(uploads, indent = 2))

    


