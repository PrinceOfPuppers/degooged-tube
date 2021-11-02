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


uploadScrapeBody = \
      ScrapeNode("gridVideoRenderer", ScrapeNum.All,[
          ScrapeNode("videoId", ScrapeNum.First,[]),
          ScrapeNode("thumbnails", ScrapeNum.First,[
              ScrapeNode("url", ScrapeNum.First,[], collapse=True)
          ]),
          ScrapeNode("publishedTimeText", ScrapeNum.First,[
              ScrapeNode("simpleText", ScrapeNum.First,[], collapse=True)
          ]),
          ScrapeNode("title", ScrapeNum.First,[
              ScrapeNode("text", ScrapeNum.First,[], collapse=True)
          ])
      ], collapse = True)

def cli():
    setupLogger()

    url = "https://www.youtube.com/c/karljobst/videos"
    uploads = YtApiList(url, 'browse', uploadScrapeBody, True)

    for upload in uploads:
        print(upload)
        print("\n")
