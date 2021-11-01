from degooged_tube.apiHacking import YoutubeApiData, scrapeJsonTree, ScrapeNode, ScrapeNum
import json
import logging
import degooged_tube.config as cfg

def setupLogger():
    stream = logging.StreamHandler()
    cfg.logger.setLevel(logging.DEBUG)
    stream.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    cfg.logger.addHandler(stream)


def cli():
    setupLogger()

    url = "https://www.youtube.com/c/karljobst/videos"
    ytapi = YoutubeApiData.fromUrl(url,'browse') 
    cfg.logger.info(ytapi)

    if ytapi is None:
        exit()

    baseKeyText = 'tabs'
    total = []
    for i in range(0,30):
        cfg.logger.info(f"iteration {i}")
        data = ytapi.getNext()
        if data == None:
            break

        res = []
        
        scrapeJsonTree(data, 
            ScrapeNode(baseKeyText,ScrapeNum.First,[
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
                ])
            ,res)

        baseKeyText = "continuationItems"
        cfg.logger.info(json.dumps(res, sort_keys=True, indent=4, separators=(',', ': ')))
        total.extend(res[0])

    cfg.logger.info("Number of Videos:", len(total))

