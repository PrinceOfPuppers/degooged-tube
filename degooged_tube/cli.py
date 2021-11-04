from degooged_tube.ytapiHacking.ytContIter import YtInitalPage
from degooged_tube.ytapiHacking.jsonScraping import ScrapeNode, ScrapeNum
from degooged_tube.ytapiHacking.YtApiList import YtApiList
import json
import logging
import degooged_tube.config as cfg

def setupLogger():
    stream = logging.StreamHandler()
    cfg.logger.setLevel(logging.DEBUG)
    stream.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    cfg.logger.addHandler(stream)


uploadScrapeFmt = \
      ScrapeNode("gridVideoRenderer", ScrapeNum.All,[
          ScrapeNode("videoId", ScrapeNum.First,[]),
          ScrapeNode("thumbnails", ScrapeNum.First,[
              ScrapeNode("url", ScrapeNum.First,[], collapse=True)
          ], rename = "thumbnail"),
          ScrapeNode("publishedTimeText", ScrapeNum.First,[
              ScrapeNode("simpleText", ScrapeNum.First,[], collapse=True)
          ], rename = "uploaded on"),
          ScrapeNode("title", ScrapeNum.First,[
              ScrapeNode("text", ScrapeNum.First,[], collapse=True)
          ])
      ], collapse = True)

commentScrapeFmt = \
      ScrapeNode("contentText", ScrapeNum.All,[
          ScrapeNode("runs", ScrapeNum.First,[
              ScrapeNode("text", ScrapeNum.All,[], collapse = True)
          ], collapse = True)
      ], collapse=True)

def uploadsCallback(res):
    for vid in res:
        print(vid)

    return res
def cli():
    setupLogger()

    uploadUrl = "https://www.youtube.com/c/karljobst/videos"
    uploadsPage = YtInitalPage.fromUrl(uploadUrl, getDataInScript = True)

    if uploadsPage is None:
        raise Exception("No Uploads Page")

    uploads = YtApiList(uploadsPage, "/youtubei/v1/browse", uploadScrapeFmt, getInitalData=True)

    upload = uploads[20]
    # print(f"Getting Commments for Upload: {upload['title']}")

    videoUrl = f"https://www.youtube.com/watch?v={upload['videoId']}"

    videoPage = YtInitalPage.fromUrl(videoUrl)
    if videoPage is None:
        raise Exception("Error Getting Page for video")

    comments = YtApiList(videoPage, '/youtubei/v1/next', commentScrapeFmt)
    print(comments[1])
    print('\n')
    print(comments[2])
    print('\n')
    print(comments[3])
    print('\n')
    print(comments[4])
    print('\n')
    print(comments[40])

