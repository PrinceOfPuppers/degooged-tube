from degooged_tube.ytapiHacking.jsonScraping import ScrapeNode, ScrapeNum
import re

####################
#  General Stuff  ##
####################

# scraping regexs for inital pages
apiKeyRe = re.compile(r'[\'\"]INNERTUBE_API_KEY[\'\"]:[\'\"](.*?)[\'\"]')
clientVersionRe = re.compile(r'[\'\"]cver[\'\"]: [\'|\"](.*?)[\'\"]')
ytInitalDataRe = re.compile(r"ytInitialData = (\{.*?\});</script>")

# inital page continuation token and apiUrl scraping 
continuationScrapeFmt = \
    ScrapeNode("continuationItemRenderer", ScrapeNum.All,[
        ScrapeNode("apiUrl", ScrapeNum.First,[]),
        ScrapeNode("token", ScrapeNum.First,[])
    ], collapse = True)

# continuation token scraping regex for continuation json (you could also use continuationScrapeFmt) 
continuationTokenRe = re.compile(r'[\'\"]token[\'\"]\s?:\s?[\'\"](.*?)[\'\"]')


# post request url for continuation chains, key is scraped from inital 
apiContinuationUrlFmt = 'https://www.youtube.com/{apiUrl}?key={key}'

# post request body for continuation chains, clientVersion is scraped from inital page, continuationToken from inital and subsequent api responses
apiContinuationBodyFmt = '''{{
    "context": {{
        "adSignalsInfo": {{
        }},
        "clickTracking": {{
        }},
        "client": {{
            "clientName": "WEB",
            "clientVersion": "{clientVersion}",
        }},
        "request": {{
        }},
        "user": {{
        }}
    }},
    "continuation": "{continuationToken}"
}}'''


# subsequent scraping formats will be wrapped by scraper nodes with these keys
continuationPageDataContainerKey = "continuationItems"
initalPageDataContainerKey = "tabs"









###############################
##  Api Route Specific Stuff  #
###############################

# Each Route Requires:
# - a url fragment to be put into apiContinuationUrlFmt (you can get a list of them using YtInitalPage.apiUrls if getInitalData = True is passed)
# - a format to use with scrapeJsonTree
# - (optional) a callback, called by onExtend in YtApiList whenever new data is requested and appended

# res in callbacks will be an array of what is dictated by the format


# uploads
uploadsApiUrl = '/youtubei/v1/browse'

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

def uploadsCallback(res):
    #for vid in res:
    #    print(vid)

    return res



# comments
commentsApiUrl = '/youtubei/v1/next'

commentScrapeFmt = \
      ScrapeNode("contentText", ScrapeNum.All,[
          ScrapeNode("runs", ScrapeNum.First,[
              ScrapeNode("text", ScrapeNum.All,[], collapse = True)
          ], collapse = True)
      ], collapse=True)

def commentCallback(res):
    for i,comment in enumerate(res):
        res[i] = ''.join(comment)

    return res


# relatedVideos
relatedVideosApiUrl = '/youtubei/v1/next'

relatedVideosScrapeFmt = \
      ScrapeNode("compactVideoRenderer", ScrapeNum.All,[
          ScrapeNode("videoId", ScrapeNum.First,[]),
          ScrapeNode("thumbnails", ScrapeNum.First,[
              ScrapeNode("url", ScrapeNum.First,[], collapse=True)
          ], rename = "thumbnail"),
          ScrapeNode("publishedTimeText", ScrapeNum.First,[
              ScrapeNode("simpleText", ScrapeNum.First,[], collapse=True)
          ], rename = "uploaded on"),
          ScrapeNode("title", ScrapeNum.First,[
              ScrapeNode("simpleText", ScrapeNum.First,[], collapse=True)
          ])
      ], collapse = True)
