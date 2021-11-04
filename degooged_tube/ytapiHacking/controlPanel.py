from degooged_tube.ytapiHacking.jsonScraping import ScrapeNode, ScrapeNum
import re

####################
#  General Stuff  ##
####################

# scraping regexs for inital pages, continuationTokenRe is also used on subsequent api responses
apiKeyRe = re.compile(r'[\'\"]INNERTUBE_API_KEY[\'\"]:[\'\"](.*?)[\'\"]')
continuationTokenRe = re.compile(r'[\'\"]token[\'\"]\s?:\s?[\'\"](.*?)[\'\"]')
clientVersionRe = re.compile(r'[\'\"]cver[\'\"]: [\'|\"](.*?)[\'\"]')
ytInitalDataRe = re.compile(r"ytInitialData = (\{.*?\});</script>")


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
# - a url fragment to be put into apiContinuationUrlFmt 
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
