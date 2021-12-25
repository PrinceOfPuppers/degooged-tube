from .jsonScraping import ScrapeNth, ScrapeAll, ScrapeElement, ScrapeAllUnion, ScrapeAllUnionNode
from typing import Union
from .helpers import tryGet, approxTimeToUnix, tryGetMultiKey, getApproximateNum
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
    ScrapeAll("continuationItemRenderer",[
        ScrapeNth("apiUrl",[]),
        ScrapeNth("token",[])
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

@dataclass 
class Thumbnail:
    width:int
    height:int
    url:str

    @classmethod
    def fromData(cls, data) -> 'Thumbnail':
        width:int  = int(tryGet(data, "width", "0"))
        height:int = int(tryGet(data, "height", "0"))
        url:str    = tryGet(data, "url")
        return cls(width, height, url)

    def __repr__(self):
        return self.url

    def __str__(self):
        return self.__repr__()





# some stuff shares scraper formats, such as uploads and recommended videos, so we create wrappers for them
def _uploadAndRelatedFmt(titleTextKey: str, durationTextContainerKey: str) -> list[ScrapeElement]:
    return [
         ScrapeNth("videoId",[]),

         ScrapeNth("thumbnails",[]),

         ScrapeNth("publishedTimeText",[
             ScrapeNth("simpleText",[], collapse=True)
         ], rename = "uploadedOn"),

         ScrapeNth("viewCountText",[
             ScrapeNth("simpleText",[], collapse=True)
         ], rename = "views"),

         ScrapeNth(durationTextContainerKey, [
             ScrapeNth("simpleText",[], collapse=True)
         ], rename = "duration"),

         ScrapeNth("title",[
             ScrapeNth(titleTextKey, [], collapse=True)
         ]),
    ]




###############################
#  Inital Page Scraping Stuff #
###############################

channelInfoScrapeFmt = \
    [
        ScrapeNth("header",[
            ScrapeNth("title",[], rename='channelName'),
            ScrapeNth("avatar",[
                ScrapeNth("thumbnails",[], collapse=True),
            ]),
            ScrapeNth("banner",[
                ScrapeNth("thumbnails",[], collapse=True),
            ], rename='banners'),
            ScrapeNth("mobileBanner",[
                ScrapeNth("thumbnails",[], collapse=True),
            ], rename='mobileBanners'),
            ScrapeNth("subscriberCountText",[
                ScrapeAll("simpleText",[], collapse=True),
            ], rename='subscribers'),
        ], collapse= True),

        ScrapeNth("metadata", [
            ScrapeNth("vanityChannelUrl",[], rename='channelUrl'),
            ScrapeNth("description",[]),
        ]),
    ]

@dataclass
class ChannelInfo:
    channelName:str
    avatar:list[Thumbnail]
    banners:list[Thumbnail]
    mobileBanners:list[Thumbnail]
    subscribers:str
    channelUrl:str
    description:str

    @classmethod
    def fromData(cls, data:dict) -> 'ChannelInfo':
        channelName:str               = data['channelName']
        avatar:list[Thumbnail]        = [Thumbnail.fromData(datum) for datum in tryGet(data, 'avatar', [])]
        banners:list[Thumbnail]       = [Thumbnail.fromData(datum) for datum in tryGet(data, 'banners', [])]
        mobileBanners:list[Thumbnail] = [Thumbnail.fromData(datum) for datum in tryGet(data, 'mobileBanners', [])]
        subscribers:str               = "".join(tryGet(data, 'subscribers', []))
        channelUrl:str                = data['channelUrl']
        description:str               = data['description']
        return cls(channelName, avatar, banners, mobileBanners, subscribers, channelUrl, description)


channelUrlSanitizationSplitsPostfix = ['?', '&', '/channels', '/channels', '/about', '/featured', '/videos']
channelUrlSanitizationSplitsPrefix = ['https', 'http']


videoInfoScrapeFmt = \
    ScrapeNth("twoColumnWatchNextResults",[

        ScrapeNth("description",[
            ScrapeAll("text",[], collapse=True),
        ]),

        ScrapeNth("videoPrimaryInfoRenderer",[
                ScrapeNth("title",[
                    ScrapeAll("text",[], collapse=True),
                ], rename = "title"),

                ScrapeNth("videoViewCountRenderer",[
                    ScrapeNth("viewCount",[
                        ScrapeNth("simpleText",[],collapse=True)
                    ],rename = "exactViews"),
                    ScrapeNth("shortViewCount",[
                        ScrapeNth("simpleText",[],collapse=True)
                    ],rename = "approxViews"),
                ], collapse = True),

                # likes
                ScrapeNth("topLevelButtons",[
                    ScrapeNth("toggleButtonRenderer",[ # assumes likes is the first button in this button list
                        ScrapeNth("defaultText",[
                            ScrapeNth("accessibilityData",[
                                ScrapeNth("label", [], rename = "exactLikes")
                            ],collapse=True),
                            ScrapeNth("simpleText", [], rename = "approxLikes")
                        ], collapse = True)
                    ], collapse = True)
                ], collapse=True)

            # RIP dislikes :c
            #ScrapeNth("sentimentBar",[
            #    ScrapeNth("tooltip",[], collapse=True)
            #],rename="likeDislike"),
            
        ], collapse = True),

        ScrapeNth("videoSecondaryInfoRenderer",[
            ScrapeNth("owner",[
                ScrapeNth("title",[
                    ScrapeNth("text",[],collapse=True)
                    ], rename = "channelName"),
                ScrapeNth("url",[],rename = 'channelUrlFragment'),
                ScrapeNth("thumbnails",[]),
            ],collapse=True),

            ScrapeNth("subscriberCountText",[
                ScrapeNth("simpleText",[], collapse=True)
            ],rename="subscribers"),
        ], collapse=True),

        ScrapeNth("dateText",[
            ScrapeNth("simpleText",[], collapse=True),
        ], rename='uploadedOn'),

        ScrapeNth("subscriberCountText",[
            ScrapeAll("simpleText",[], collapse=True),
        ], rename='subscribers'),
    ],collapse=True)

@dataclass
class VideoInfo:
    description:str
    title:str

    views:str
    viewsNum:int

    likes:str
    likesNum:int

    channelName:str
    channelUrlFragment:str
    channelUrl:str

    uploadedOn:str
    subscribers:str
    thumbnails:list

    @classmethod
    def fromData(cls, data:dict) -> 'VideoInfo':
        description:str             = "".join(tryGet(data, 'description', []))
        title:str                   = "".join(tryGet(data, 'title', []))

        views:str                   = tryGetMultiKey(data, "0", "exactViews", "approxViews")
        viewsNum:int                = getApproximateNum(views)
        likes:str                   = tryGetMultiKey(data, "0", "exactLikes", "approxLikes")
        likesNum:int                = getApproximateNum(likes)

        channelName:str             = tryGet(data, 'channelName')
        channelUrlFragment:str      = data['channelUrlFragment']
        channelUrl:str              = 'https://www.youtube.com' + channelUrlFragment
        uploadedOn:str              = data['uploadedOn']
        subscribers:str             = tryGet(data, 'subscribers', "0")
        thumbnails:list[Thumbnail]  = [Thumbnail.fromData(datum) for datum in tryGet(data, 'thumbnails', [])]

        return cls(description, title, views, viewsNum, likes, likesNum, channelName, channelUrlFragment, channelUrl, uploadedOn, subscribers, thumbnails, )


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

uploadScrapeFmt = ScrapeAll("gridVideoRenderer", _uploadAndRelatedFmt("text", "thumbnailOverlayTimeStatusRenderer"), collapse = True)

@dataclass
class Upload:
    videoId:str
    url:str
    unixTime:int
    thumbnails:list[Thumbnail]
    uploadedOn:str
    views:str
    duration:str
    title:str
    channelName:str
    channelUrl:str

    @classmethod
    def fromData(cls, data:dict) -> 'Upload':
        videoId:str                 = data['videoId']
        uploadedOn:str              = data['uploadedOn']

        url:str                     = 'https://www.youtube.com/watch?v=' + videoId
        unixTime:int                = approxTimeToUnix(currentTime, uploadedOn)
        thumbnails:list[Thumbnail]  = [Thumbnail.fromData(datum) for datum in tryGet(data, 'thumbnails', [])]
        views:str                   = data['views']
        duration:str                = data['duration']
        title:str                   = data['title']

        # the following are added by subbox
        channelName:str = ''
        channelUrl:str = ''
        return cls(videoId, url, unixTime, thumbnails, uploadedOn, views, duration, title, channelName, channelUrl)
    
    def __repr__(self):
        return f'{self.title}\n     > {self.channelName} | {self.duration} | {self.uploadedOn} | {self.views}\n'

    def __str__(self):
        return self.__repr__()



# >Comments< #
commentsApiUrl = '/youtubei/v1/next'

commentScrapeFmt  = \
      ScrapeAll("comment",[
          ScrapeNth("contentText",[
              ScrapeNth("runs",[
                  ScrapeAll("text",[], collapse = True)
              ], rename = "commentRuns")
          ], collapse=True),

          ScrapeNth("authorText",[
              ScrapeNth("simpleText",[], collapse = True)
          ], rename = "author"),

          ScrapeNth("thumbnails",[], rename = "avatar")
      ], collapse = True)

@dataclass
class Comment:
    author:str
    comment:str
    avatar:list[Thumbnail]

    @classmethod
    def fromData(cls, data):
        author:str              = tryGet(data, 'author')
        comment:str             = "".join(tryGet(data, 'commentRuns', []))
        avatar:list[Thumbnail]  = [Thumbnail.fromData(datum) for datum in tryGet(data, 'avatar', [])]
        return cls(author, comment, avatar)

    def __repr__(self):
        return f"> {self.author} \n{self.comment}"

    def __str__(self):
        return self.__repr__()




# >RelatedVideos< #
relatedVideosApiUrl = '/youtubei/v1/next'

relatedVideosScrapeFmt = \
    ScrapeAll("compactVideoRenderer", [
        *_uploadAndRelatedFmt("simpleText", "lengthText"), 
        ScrapeNth("longBylineText", [
            ScrapeNth("text", [], collapse = True),
        ], rename = "channelName"),
        ScrapeNth("longBylineText", [
            ScrapeNth("url", [], collapse = True)
        ],rename = "channelUrlFragment")
    ], collapse = True)

@dataclass
class RelatedVideo:
    videoId:str
    url:str
    unixTime:int
    thumbnails:list[Thumbnail]
    uploadedOn:str
    views:str
    duration:str
    title:str

    channelName:str
    channelUrlFragment:str
    channelUrl:str

    @classmethod
    def fromData(cls, data:dict) -> 'RelatedVideo':
        videoId:str                 = data['videoId']
        url:str                     = 'https://www.youtube.com/watch?v=' + data['videoId']
        unixTime:int                = approxTimeToUnix(currentTime, data['uploadedOn'])
        thumbnails:list[Thumbnail]  = [Thumbnail.fromData(datum) for datum in tryGet(data, 'thumbnails', [])]
        uploadedOn:str              = data['uploadedOn']
        views:str                   = data['views']
        duration:str                = data['duration']
        title:str                   = data['title']

        channelName:str = tryGet(data, "channelName")
        channelUrlFragment:str = tryGet(data, "channelUrlFragment")
        channelUrl:str = 'https://www.youtube.com' + channelUrlFragment

        return cls(videoId, url, unixTime, thumbnails, uploadedOn, views, duration, title, channelName, channelUrlFragment, channelUrl)
    
    def __repr__(self):
        return f'{self.title}\n     > {self.channelName} | {self.duration} | {self.uploadedOn} | {self.views}\n'

    def __str__(self):
        return self.__repr__()



# >Search< #
searchUrl = "https://www.youtube.com/results?search_query="
searchApiUrl = '/youtubei/v1/search'
searchFilterSelectedStatus = "FILTER_STATUS_SELECTED"


# Search Filters
searchFilterScrapeFmt = \
    ScrapeAll("searchFilterGroupRenderer",[
            ScrapeNth("title",[
                ScrapeNth("simpleText", [],  collapse=True),
            ], rename= "searchType"),

            ScrapeNth("filters",[
                ScrapeAll("searchFilterRenderer", [

                    ScrapeNth("label",[
                        ScrapeNth("simpleText", [],  collapse=True),
                    ]),

                    ScrapeNth("url", [], rename="searchUrlFragment"),
                    ScrapeNth("status", [], rename="searchUrlFragment", optional = True)

                ],  collapse=True),
            ]),
    ], collapse= True)

@dataclass
class SearchFilter:
    label:str
    searchUrlFragment:str
    selected:bool

    def __repr__(self):
        s = f"{self.label}"

        if self.selected:
            s = f"> {s} <"

        return s

    def __str__(self):
        return self.__repr__()

@dataclass
class SearchType:
    searchType:str
    filters:list[SearchFilter]

    @classmethod
    def fromData(cls, data:dict):
        searchType = tryGet(data, 'searchType')
        filterData = tryGet(data, 'filterData', [])

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

    def __len__(self):
        return len(self.filters)

    def __repr__(self):
        return self.searchType

    def __str__(self):
        return self.__repr__()



searchScrapeFmt = \
    ScrapeNth("twoColumnSearchResultsRenderer",[
        ScrapeNth("itemSectionRenderer",[
            ScrapeAllUnion("", [

                ScrapeAllUnionNode("channelRenderer", [

                    ScrapeNth("title",[
                        ScrapeNth("text",[],collapse=True)
                    ], rename = 'channelName'),

                    ScrapeNth("browseEndpoint",[
                        ScrapeNth("canonicalBaseUrl", [],  collapse=True),
                    ], rename = 'channelUrlFragment'),

                    ScrapeNth("thumbnails",[], rename = 'channelIcons'),

                    ScrapeNth("descriptionSnippet",[
                        ScrapeNth("text", [],  collapse=True),
                    ], rename = 'channelDescription'),

                    ScrapeNth("subscriberCountText",[
                        ScrapeNth("simpleText",[],collapse=True)
                    ], rename = "subscribers"),

                    ScrapeNth("videoCountText",[
                        ScrapeNth("runs",[
                            ScrapeAll("text",[], collapse=True)
                        ],collapse=True)
                    ], rename = "videoCount"),

                ], rename="channel"),


                ScrapeAllUnionNode("videoRenderer",[
                    ScrapeNth("title",[
                        ScrapeNth("text",[],collapse=True)
                    ]),

                    ScrapeNth("longBylineText",[
                        ScrapeNth("text", [],  collapse=True),
                    ], rename= "channelName"),

                    ScrapeNth("longBylineText",[
                        ScrapeNth("canonicalBaseUrl", [], collapse=True)
                    ],rename="channelUrlFragment"),

                    ScrapeNth("videoId",[]),

                    ScrapeNth("thumbnails",[]),

                    ScrapeNth("viewCountText",[
                        ScrapeNth("simpleText",[],collapse=True)
                    ], rename="views"),

                    ScrapeNth("lengthText",[
                        ScrapeNth("simpleText",[],collapse=True)
                    ], rename="duration"),

                    ScrapeNth("publishedTimeText",[
                        ScrapeNth("simpleText",[],collapse=True)
                    ], rename="uploadedOn"),

                ], rename = "video")

        ], collapse = True)
    ], collapse= True)
], collapse= True)

def SearchElementFromData(data:dict):
    if "video" in data:
        return SearchVideo.fromData(data["video"])
    if "channel" in data:
        return SearchChannel.fromData(data["channel"])
    raise Exception("Should Never Occur")

@dataclass
class SearchVideo:
    title:str
    channelName:str
    channelUrlFragment:str
    channelUrl:str
    videoId:str
    url:str
    thumbnails: list
    views:str
    duration:str
    uploadedOn:str

    @classmethod
    def fromData(cls, data:dict) -> Union['SearchVideo', None]:
        try:
            videoId = data['videoId']
            title   = data["title"]
            url = 'https://www.youtube.com/watch?v=' + videoId
            channelUrlFragment = data["channelUrlFragment"]
            channelUrl = 'https://www.youtube.com' + channelUrlFragment
            
        except KeyError:
            return None

        channelName                 = tryGet(data, "name")
        channelUrlFragment          = tryGet(data, "channelUrlFragment")
        videoId                     = tryGet(data, "videoId")
        thumbnails:list[Thumbnail]  = [Thumbnail.fromData(datum) for datum in tryGet(data, 'thumbnails', [])]
        views                       = tryGet(data, "views")
        duration                    = tryGet(data, "duration")
        uploadedOn                  = tryGet(data, "uploadedOn")

        return cls(title, channelName, channelUrlFragment, channelUrl, videoId, url, thumbnails, views, duration, uploadedOn)

    def __repr__(self):
        return f'{self.title}\n     > {self.channelName} | {self.duration} | {self.uploadedOn} | {self.views}\n'

    def __str__(self):
        return self.__repr__()

@dataclass
class SearchChannel:
    channelName:str
    channelUrlFragment:str
    channelUrl:str
    channelIcons: list
    channelDescription:str
    subscribers:str
    videoCount:str

    @classmethod
    def fromData(cls, data:dict) -> Union['SearchChannel', None]:
        try:
            channelName        = data['channelName']
            channelUrlFragment = data['channelUrlFragment ']
            channelUrl         = 'https://www.youtube.com' + channelUrlFragment
        except KeyError:
            return None

        channelIcons       = tryGet(data, 'channelIcons', [])
        channelDescription = tryGet(data, 'channelDescription')
        subscribers        = tryGet(data, 'subscribers')
        videoCount         = " ".join(tryGet(data, 'videoCount', []))

        return cls(channelName, channelUrlFragment, channelUrl, channelIcons, channelDescription, subscribers, videoCount)

    def __repr__(self):
        return f'{self.channelName}\n     > {self.subscribers} | {self.videoCount}'

    def __str__(self):
        return self.__repr__()
