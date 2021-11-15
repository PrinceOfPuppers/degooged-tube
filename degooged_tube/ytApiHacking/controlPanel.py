from .jsonScraping import ScrapeNode, ScrapeNum
import re

####################
#  General Stuff  ##
####################

ytTimeConversion = {
    "second":  1,
    "seconds": 1,

    "minute":  60,
    "minutes": 60,

    "hour":    3600,
    "hours":   3600,

    "day":     86400,
    "days":    86400,

    "week":    604800,
    "weeks":   604800,

    "month":   2419200,
    "months":  2419200,

    "year":    29030400,
    "years":   29030400,
}
timeDelineations = "|".join(ytTimeConversion.keys())
approxTimeRe = re.compile(r"(\d+)\s+("+timeDelineations +r")\s+ago", re.I)

channelVideoPath = '/videos'

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
def _videoDataFmt(titleTextKey: str, durationTextContainerKey: str):
    return [
        ScrapeNode("videoId", ScrapeNum.First,[]),

         #ScrapeNode("thumbnails", ScrapeNum.All,[]),

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
         ]),
         ScrapeNode("longBylineText", ScrapeNum.First,[
             ScrapeNode("canonicalBaseUrl", ScrapeNum.First,[], collapse=True)
         ], rename = "channelUrlFragment")
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


videoInfoScrapeFmt = \
    ScrapeNode("twoColumnWatchNextResults", ScrapeNum.First,[
        ScrapeNode("description", ScrapeNum.First,[
            ScrapeNode("text", ScrapeNum.All,[], collapse=True),
        ]),

        ScrapeNode("videoPrimaryInfoRenderer", ScrapeNum.First,[
                ScrapeNode("title", ScrapeNum.First,[]),
                ScrapeNode("videoViewCountRenderer", ScrapeNum.First,[
                    ScrapeNode("viewCount", ScrapeNum.First,[
                        ScrapeNode("simpleText", ScrapeNum.First,[],collapse=True)
                    ],),
            ], collapse = True),
            ScrapeNode("sentimentBar", ScrapeNum.First,[
                ScrapeNode("tooltip", ScrapeNum.First,[], collapse=True)
            ],rename="likeDislike"),
        ]),

        ScrapeNode("videoSecondaryInfoRenderer", ScrapeNum.First,[
            ScrapeNode("owner", ScrapeNum.First,[
                ScrapeNode("title", ScrapeNum.First,[
                    ScrapeNode("text", ScrapeNum.First,[],collapse=True)
                    ], rename = "channelName"),
                ScrapeNode("url", ScrapeNum.First,[],rename = 'channelUrlFragment'),
                ScrapeNode("thumbnails", ScrapeNum.First,[]),
            ],collapse=True),

            ScrapeNode("subscriberCountText", ScrapeNum.First,[
                ScrapeNode("simpleText", ScrapeNum.First,[], collapse=True)
            ],rename="subscriberCount"),
        ]),

        ScrapeNode("dateText", ScrapeNum.First,[
            ScrapeNode("simpleText", ScrapeNum.First,[], collapse=True),
        ], rename='date'),

        ScrapeNode("subscriberCountText", ScrapeNum.First,[
            ScrapeNode("simpleText", ScrapeNum.All,[], collapse=True),
        ], rename='subscribers'),
    ],collapse=True)


############################################
##  Continuation Api Route Specific Stuff  #
############################################

# Each Route Requires:
# - a url fragment to be put into apiContinuationUrlFmt (you can get a list of them using YtInitalPage.apiUrls if getInitalData = True is passed)
# - a format to use with scrapeJsonTree
# - (optional) a callback, called by onExtend in YtApiList whenever new data is requested and appended (defined in .__init__.py)

# res in callbacks will be an array of what is dictated by the format



# >Uploads< #
uploadsApiUrl = '/youtubei/v1/browse'

uploadScrapeFmt = ScrapeNode("gridVideoRenderer", ScrapeNum.All, _videoDataFmt("text", "thumbnailOverlayTimeStatusRenderer"), collapse = True)



# >Comments< #
commentsApiUrl = '/youtubei/v1/next'

commentScrapeFmt = \
      ScrapeNode("contentText", ScrapeNum.All,[
          ScrapeNode("runs", ScrapeNum.First,[
              ScrapeNode("text", ScrapeNum.All,[], collapse = True)
          ], collapse = True)
      ], collapse=True)



# >RelatedVideos< #
relatedVideosApiUrl = '/youtubei/v1/next'

relatedVideosScrapeFmt = ScrapeNode("compactVideoRenderer", ScrapeNum.All, _videoDataFmt("simpleText", "lengthText"), collapse = True)

