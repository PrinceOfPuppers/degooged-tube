from .jsonScraping import ScrapeNode, ScrapeNum
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





# some stuff shares scraper formats, such as uploads and recommended videos, so we create wrappers for them
def videoDataFmt(titleTextKey: str, durationTextContainerKey: str):
    return [
        ScrapeNode("videoId", ScrapeNum.First,[]),

         ScrapeNode("thumbnails", ScrapeNum.All,[]),

         ScrapeNode("publishedTimeText", ScrapeNum.First,[
             ScrapeNode("simpleText", ScrapeNum.First,[], collapse=True)
         ], rename = "uploaded on"),

         ScrapeNode("viewCountText", ScrapeNum.First,[
             ScrapeNode("simpleText", ScrapeNum.First,[], collapse=True)
         ], rename = "views"),

         ScrapeNode(durationTextContainerKey, ScrapeNum.First,[
             ScrapeNode("simpleText", ScrapeNum.First,[], collapse=True)
         ], rename = "duration"),

         ScrapeNode("title", ScrapeNum.First,[
             ScrapeNode(titleTextKey, ScrapeNum.First,[], collapse=True)
         ])
    ]




###############################
#  Inital Page Scraping Stuff #
###############################

channelInfoScrapeFmt = \
    ScrapeNode("header", ScrapeNum.First,[
        ScrapeNode("title", ScrapeNum.First,[], rename='name'),
        ScrapeNode("canonicalBaseUrl", ScrapeNum.First,[], rename='baseUrl'),
        ScrapeNode("avatar", ScrapeNum.First,[
            ScrapeNode("thumbnails", ScrapeNum.All,[], collapse=True),
        ]),
        ScrapeNode("banner", ScrapeNum.First,[
            ScrapeNode("thumbnails", ScrapeNum.All,[], collapse=True),
        ], rename='banners'),
        ScrapeNode("mobileBanner", ScrapeNum.First,[
            ScrapeNode("thumbnails", ScrapeNum.All,[], collapse=True),
        ], rename='mobileBanners'),
        ScrapeNode("subscriberCountText", ScrapeNum.First,[
            ScrapeNode("simpleText", ScrapeNum.All,[], collapse=True),
        ], rename='subscribers'),
    ],collapse=True)


channelUrlSanitizationSplits = ['?', '&', '/channels', '/channels', '/about', '/featured', '/videos']


############################################
##  Continuation Api Route Specific Stuff  #
############################################

# Each Route Requires:
# - a url fragment to be put into apiContinuationUrlFmt (you can get a list of them using YtInitalPage.apiUrls if getInitalData = True is passed)
# - a format to use with scrapeJsonTree
# - (optional) a callback, called by onExtend in YtApiList whenever new data is requested and appended

# res in callbacks will be an array of what is dictated by the format



# >Uploads< #
uploadsApiUrl = '/youtubei/v1/browse'

uploadScrapeFmt = \
      ScrapeNode("gridVideoRenderer", ScrapeNum.All,videoDataFmt("text", "thumbnailOverlayTimeStatusRenderer"), collapse = True)

def uploadsCallback(res):
    #for vid in res:
    #    print(vid)
    return res


# >Comments< #
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



# >RelatedVideos< #
relatedVideosApiUrl = '/youtubei/v1/next'

relatedVideosScrapeFmt = \
      ScrapeNode("compactVideoRenderer", ScrapeNum.All, videoDataFmt("simpleText", "lengthText"), collapse = True)

