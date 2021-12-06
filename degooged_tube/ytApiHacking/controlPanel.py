from .jsonScraping import ScrapeNode, ScrapeNum
from typing import Union
from .helpers import tryGet, approxTimeToUnix
import re
from dataclasses import dataclass

import time
currentTime = int(time.time())

####################
#  General Stuff  ##
####################
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


# subsequent scraping formats will be wrapped by scraper nodes with these keys (unless specified otherwise)
continuationPageDataContainerKey = "continuationItems"
initalPageDataContainerKey = "contents"



# some stuff shares scraper formats, such as uploads and recommended videos, so we create wrappers for them
def _uploadAndRelatedFmt(titleTextKey: str, durationTextContainerKey: str):
    return [
         ScrapeNode("videoId", ScrapeNum.First,[]),

         ScrapeNode("thumbnails", ScrapeNum.All,[]),

         ScrapeNode("publishedTimeText", ScrapeNum.First,[
             ScrapeNode("simpleText", ScrapeNum.First,[], collapse=True)
         ], rename = "uploadedOn"),

         ScrapeNode("viewCountText", ScrapeNum.First,[
             ScrapeNode("simpleText", ScrapeNum.First,[], collapse=True)
         ], rename = "views"),

         ScrapeNode(durationTextContainerKey, ScrapeNum.First,[
             ScrapeNode("simpleText", ScrapeNum.First,[], collapse=True)
         ], rename = "duration"),

         ScrapeNode("title", ScrapeNum.First,[
             ScrapeNode(titleTextKey, ScrapeNum.First,[], collapse=True)
         ]),
    ]




###############################
#  Inital Page Scraping Stuff #
###############################

channelInfoScrapeFmt = \
    [
        ScrapeNode("header", ScrapeNum.First,[
            ScrapeNode("title", ScrapeNum.First,[], rename='channelName'),
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
        ], collapse= True),

        ScrapeNode("metadata", ScrapeNum.First, [
            ScrapeNode("vanityChannelUrl", ScrapeNum.First,[], rename='channelUrl'),
            ScrapeNode("description", ScrapeNum.First,[]),
        ]),
    ]

@dataclass
class ChannelInfo:
    channelName:str
    avatar:list
    banners:list
    mobileBanners:list
    subscribers:str
    channelUrl:str
    description:str

    @classmethod
    def fromData(cls, data:dict) -> 'ChannelInfo':
        channelName:str        = data['channelName']
        avatar:list            = data['avatar']
        banners:list           = data['banners']
        mobileBanners:list     = data['mobileBanners']
        subscribers:str        = data['subscribers']
        channelUrl:str         = data['channelUrl']
        description:str        = data['description']
        return cls(channelName, avatar, banners, mobileBanners, subscribers, channelUrl, description)


channelUrlSanitizationSplitsPostfix = ['?', '&', '/channels', '/channels', '/about', '/featured', '/videos']
channelUrlSanitizationSplitsPrefix = ['https', 'http']


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
            #ScrapeNode("sentimentBar", ScrapeNum.First,[
            #    ScrapeNode("tooltip", ScrapeNum.First,[], collapse=True)
            #],rename="likeDislike"),
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
# - (optional) a class to unpack the json into, and deal with cases where data is missing

# wrapper funcitons to get this data will be in __init__.py, along with the onExtend functions passed to ytapilist

# res in callbacks will be an array of what is dictated by the format



# >Uploads< #
uploadsApiUrl = '/youtubei/v1/browse'

uploadScrapeFmt = ScrapeNode("gridVideoRenderer", ScrapeNum.All, _uploadAndRelatedFmt("text", "thumbnailOverlayTimeStatusRenderer"), collapse = True)

@dataclass
class Upload:
    videoId:str
    url:str
    unixTime:int
    thumbnails:dict
    uploadedOn:str
    views:str
    duration:str
    title:str
    channelName:str
    channelUrl:str

    @classmethod
    def fromData(cls, data:dict) -> 'Upload':
        videoId:str            = data['videoId']
        url:str                = 'https://www.youtube.com/watch?v=' + data['videoId']
        unixTime:int           = approxTimeToUnix(currentTime, data['uploadedOn'])
        thumbnails:dict        = data['thumbnails']
        uploadedOn:str         = data['uploadedOn']
        views:str              = data['views']
        duration:str           = data['duration']
        title:str              = data['title']

        # the following are added by subbox
        channelName:str = ''
        channelUrl:str = ''
        return cls(videoId, url, unixTime, thumbnails, uploadedOn, views, duration, title, channelName, channelUrl)
    
    def __repr__(self):
        return f'{self.title}\n     > {self.channelName} - {self.views}'

    def __str__(self):
        return self.__repr__()



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
relatedVideosScrapeFmt = ScrapeNode("compactVideoRenderer", ScrapeNum.All, _uploadAndRelatedFmt("simpleText", "lengthText"), collapse = True)



# >Search< #
searchUrl = "https://www.youtube.com/results?search_query="
searchApiUrl = '/youtubei/v1/search'
searchFilterSelectedStatus = "FILTER_STATUS_SELECTED"


# Search Filters
searchFilterScrapeFmt = \
    ScrapeNode("searchFilterGroupRenderer", ScrapeNum.All,[
            ScrapeNode("title", ScrapeNum.First,[
                ScrapeNode("simpleText", ScrapeNum.First, [],  collapse=True),
            ], rename= "searchType"),

            ScrapeNode("filters", ScrapeNum.First,[
                ScrapeNode("searchFilterRenderer", ScrapeNum.All, [

                    ScrapeNode("label", ScrapeNum.First,[
                        ScrapeNode("simpleText", ScrapeNum.First, [],  collapse=True),
                    ]),

                    ScrapeNode("url", ScrapeNum.First, [], rename="searchUrlFragment"),
                    ScrapeNode("status", ScrapeNum.First, [], rename="searchUrlFragment", optional = True)

                ],  collapse=True),
            ]),
    ], collapse= True)

@dataclass
class SearchFilter:
    label:str
    searchUrlFragment:str
    selected:bool

@dataclass
class SearchType:
    searchType:str
    filters:list[SearchFilter]

    @classmethod
    def fromData(cls, data:dict):
        try:
            searchType = data['searchType']
        except KeyError:
            searchType = ''

        try:
            filterData = data['filters']
        except KeyError:
            filterData = []

        filters = []
        for f in filterData:
            try:
                label = f['label']
                searchUrlFragment = f['searchUrlFragment']
            except KeyError:
                continue

            try:
                selected = f['status'] == searchFilterSelectedStatus
            except KeyError:
                selected = False

            filters.append(SearchFilter(label, searchUrlFragment, selected))

        return cls(searchType, filters)




searchVideoScrapeFmt = \
    ScrapeNode("twoColumnSearchResultsRenderer", ScrapeNum.First,[
        ScrapeNode("itemSectionRenderer", ScrapeNum.First,[
            ScrapeNode("videoRenderer", ScrapeNum.All,[
                ScrapeNode("title", ScrapeNum.First,[
                    ScrapeNode("text", ScrapeNum.First,[],collapse=True)
                ]),

                ScrapeNode("longBylineText", ScrapeNum.First,[
                    ScrapeNode("text", ScrapeNum.First, [],  collapse=True),
                ], rename= "channelName"),

                ScrapeNode("longBylineText", ScrapeNum.First,[
                    ScrapeNode("canonicalBaseUrl", ScrapeNum.First, [], collapse=True)
                ],rename="channelUrlFragment"),

                ScrapeNode("videoId", ScrapeNum.First,[]),

                ScrapeNode("thumbnails", ScrapeNum.First,[]),

                ScrapeNode("viewCountText", ScrapeNum.First,[
                    ScrapeNode("simpleText", ScrapeNum.First,[],collapse=True)
                ], rename="views"),

                ScrapeNode("lengthText", ScrapeNum.First,[
                    ScrapeNode("simpleText", ScrapeNum.First,[],collapse=True)
                ], rename="duration"),

                ScrapeNode("publishedTimeText", ScrapeNum.First,[
                    ScrapeNode("simpleText", ScrapeNum.First,[],collapse=True)
                ], rename="uploadedOn"),
            ], collapse = True)
        ], collapse = True)
    ], collapse= True)

@dataclass
class SearchVideo:
    title:str
    channelName:str
    channelUrlFragment:str
    videoId:str
    thumbnails: list
    views:str
    duration:str
    uploadedOn:str

    @classmethod
    def fromData(cls, data:dict) -> Union['SearchVideo', None]:
        try:
            videoId = data['videoId']
            title   = data["title"]
        except KeyError:
            return None

        channelName        = tryGet(data, "name")
        channelUrlFragment = tryGet(data, "channelUrlFragment")
        videoId            = tryGet(data, "videoId")
        thumbnails         = tryGet(data, "thumbnails", [])
        views              = tryGet(data, "views")
        duration           = tryGet(data, "duration")
        uploadedOn         = tryGet(data, "uploadedOn")

        return cls(title, channelName, channelUrlFragment, videoId, thumbnails, views, duration, uploadedOn)


searchChannelScrapeFmt = \
    ScrapeNode("contents", ScrapeNum.First,[

        ScrapeNode("title", ScrapeNum.First,[
            ScrapeNode("text", ScrapeNum.First,[],collapse=True)
        ], rename = 'channelName'),

        ScrapeNode("browseEndpoint", ScrapeNum.First,[
            ScrapeNode("canonicalBaseUrl", ScrapeNum.First, [],  collapse=True),
        ], rename = 'channelUrlFragment'),

        ScrapeNode("thumbnails", ScrapeNum.First,[
            ScrapeNode("text", ScrapeNum.First, [],  collapse=True),
        ], rename = 'channelIcons'),

        ScrapeNode("descriptionSnippet", ScrapeNum.First,[
            ScrapeNode("text", ScrapeNum.First, [],  collapse=True),
        ], rename = 'channelDescription'),

        ScrapeNode("subscriberCountText", ScrapeNum.First,[
            ScrapeNode("simpleText", ScrapeNum.First,[],collapse=True)
        ], rename = "subscribers"),

        ScrapeNode("videoCountText", ScrapeNum.First,[
            ScrapeNode("runs", ScrapeNum.First,[
                ScrapeNode("text", ScrapeNum.All,[], collapse=True)
            ],collapse=True)
        ], rename = "videoCount"),

    ], collapse= True)


@dataclass
class SearchChannel:
    channelName:str
    channelUrlFragment:str
    channelIcons: list
    channelDescription:str
    subscribers:str
    videoCount:str

    @classmethod
    def fromData(cls, data:dict) -> Union['SearchChannel', None]:
        try:
            channelName        = data['channelName']
            channelUrlFragment = data['channelUrlFragment ']
        except KeyError:
            return None

        channelIcons       = tryGet(data, 'channelIcons', [])
        channelDescription = tryGet(data, 'channelDescription')
        subscribers        = tryGet(data, 'subscribers')
        videoCount         = " ".join(tryGet(data, 'videoCount', [""]))

        return cls(channelName, channelUrlFragment, channelIcons, channelDescription, subscribers, videoCount)
