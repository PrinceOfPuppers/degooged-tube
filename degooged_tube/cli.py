from degooged_tube.ytapiHacking.ytContIter import YtContIter
from degooged_tube.ytapiHacking.jsonScraping import scrapeJsonTree, ScrapeNode, ScrapeNum
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

def cli():
    setupLogger()

    uploadUrl = "https://www.youtube.com/c/karljobst/videos"
    uploads = YtApiList(uploadUrl, 'browse', uploadScrapeFmt, True)
    print(uploads.prettyString())

    commentUrl = "https://www.youtube.com/watch?v=wZW2JFO4Jz4"
    comments = YtApiList(commentUrl, 'next', commentScrapeFmt, False)
    print(comments[1])
    print('\n')
    print(comments[2])
    print('\n')
    print(comments[3])
    print('\n')
    print(comments[4])
    print('\n')
    print(comments[40])

