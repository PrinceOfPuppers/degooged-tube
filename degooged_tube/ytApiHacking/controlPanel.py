from .jsonScraping import ScrapeNth, ScrapeAll, ScrapeElement, ScrapeAllUnion, ScrapeAllUnionNode, ScrapeUnion, ScrapeLongest
from typing import Union
from .helpers import tryGet, approxTimeToUnix, tryGetMultiKey, getApproximateNum, jsonRegex
import re
from dataclasses import dataclass

import degooged_tube.config as cfg

import time
currentTime = int(time.time())

####################
#  General Stuff  ##
####################
channelVideoPath = '/videos'
channelPlaylistsPath = '/playlists'

# scraping regexs for inital pages
apiKeyRe = re.compile(jsonRegex("INNERTUBE_API_KEY", "(.*?)"))
clientVersionRe = re.compile(jsonRegex("key", "cver", "value", "(.*?)" , surroundingBrace = True))
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
        url:str    = "https:" + tryGet(data, "url").strip('http:').strip("https:")
        return cls(width, height, url)

    def __repr__(self):
        return self.url

    def __str__(self):
        return self.__repr__()




def _isLive(text):
    return text.lower() == "live"

# some stuff shares scraper formats, such as uploads, recommended, and playlist videos, so we create wrappers for them
def _uploadAndRelatedFmt(titleTextKey: str, durationTextContainerKey: str, 
                         includeViewCount = True, includePublishedTime = True) -> list[ScrapeElement]:
    l:list[ScrapeElement] = [
         ScrapeNth("videoId",[]),

         ScrapeNth("thumbnails",[]),

         ScrapeNth(durationTextContainerKey, [
             ScrapeNth("simpleText",[], collapse=True)
         ], rename = "duration"),

         ScrapeNth("title",[
             ScrapeNth(titleTextKey, [], collapse=True)
         ]),
    ]

    if includePublishedTime:
        l.append(
             ScrapeUnion([
                 # not currently live
                 ScrapeNth("publishedTimeText",[
                     ScrapeNth("simpleText",[], collapse=True)
                 ], rename = "uploadedOn"),

                 # live
                 ScrapeNth("thumbnailOverlayTimeStatusRenderer",[
                     ScrapeNth("label",[], collapse=True, dataCondition = _isLive)
                 ], rename = "uploadedOn"),
             ])
        )
    if includeViewCount:
        l.append(
             ScrapeNth("viewCountText",[
                 ScrapeNth("simpleText",[], collapse=True)
             ], rename = "views"),
        )

    return l




###############################
#  Inital Page Scraping Stuff #
###############################

channelInfoScrapeFmt = \
    [
        ScrapeNth("c4TabbedHeaderRenderer",[
            ScrapeNth("title",[], rename='channelName'),
            ScrapeNth("channelId",[], rename='channelId'),
            ScrapeNth("avatar",[
                ScrapeNth("thumbnails",[], collapse=True),
            ]),
            ScrapeNth("banner",[
                ScrapeNth("thumbnails",[], collapse=True, optional = True),
            ], rename='banners'),
            ScrapeNth("mobileBanner",[
                ScrapeNth("thumbnails",[], collapse=True, optional = True),
            ], rename='mobileBanners'),
            ScrapeNth("subscriberCountText",[
                ScrapeAll("simpleText",[], collapse=True, optional = True),
            ], rename='subscribers'),
        ], collapse= True),

        ScrapeNth("metadata", [
            ScrapeNth("vanityChannelUrl",[], rename='channelUrl'),
            ScrapeNth("description",[], optional = True),
            ScrapeNth("externalId",[]), # duplicate of channelId used as a backup
        ], collapse = True),
    ]

@dataclass
class ChannelInfo:
    channelName:str
    channelId:str
    avatar:list[Thumbnail]
    banners:list[Thumbnail]
    mobileBanners:list[Thumbnail]
    subscribers:str
    channelUrl:str
    description:str

    @classmethod
    def fromData(cls, data:dict) -> 'ChannelInfo':
        data = {**data[0], **data[1]}

        channelName:str               = tryGet(data, 'channelName')
        channelId:str                 = tryGetMultiKey(data, '', 'channelId', 'externalId')
        avatar:list[Thumbnail]        = [Thumbnail.fromData(datum) for datum in tryGet(data, 'avatar', [])]
        banners:list[Thumbnail]       = [Thumbnail.fromData(datum) for datum in tryGet(data, 'banners', [])]
        mobileBanners:list[Thumbnail] = [Thumbnail.fromData(datum) for datum in tryGet(data, 'mobileBanners', [])]
        subscribers:str               = "".join(tryGet(data, 'subscribers', []))
        channelUrl:str                = tryGet(data, 'channelUrl')
        description:str               = tryGet(data, 'description')

        return cls(channelName, channelId, avatar, banners, mobileBanners, subscribers, channelUrl, description)


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
                    ScrapeNth("text",[], rename="channelName"),
                    ScrapeNth("url",[], rename = 'channelUrlFragment'),
                    ScrapeNth("browseId",[], rename = 'channelId'),
                ], collapse = True),

                ScrapeNth("thumbnails",[], rename="avatar"),
            ],collapse=True),

            ScrapeNth("navigationEndpoint",[
                ScrapeNth("browseId",[], rename = 'channelIdBackup'),
            ],collapse=True),

            ScrapeNth("subscriberCountText",[
                ScrapeNth("simpleText",[], collapse=True)
            ],rename="subscribers"),
        ], collapse=True),

        ScrapeNth("dateText",[
            ScrapeNth("simpleText",[], collapse=True),
        ], rename='uploadedOn'),

        ScrapeNth("subscriberCountText",[
            ScrapeNth("simpleText",[], collapse=True),
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
    channelId:str

    avatar:list[Thumbnail]

    uploadedOn:str
    subscribers:str

    @classmethod
    def fromData(cls, data:dict) -> Union['VideoInfo', None]:
        try:
            channelUrlFragment:str      = data['channelUrlFragment']
            uploadedOn:str              = data['uploadedOn']

            channelId:str               = tryGet(data, "channelId")
            if not channelId:
                channelId = data["channelIdBackup"] # if this doesn't work, we raise the key error

        except KeyError as e:
            if cfg.testing:
                raise Exception(f'Missing Required Key "{e.args[0]}"\nFrom Data: {data}')
            cfg.logger.debug(f'In {cls.__name__}.fromData(), Data is Missing Required Key "{e.args[0]}"')
            return None

        description:str             = "".join(tryGet(data, 'description', []))
        title:str                   = "".join(tryGet(data, 'title', []))
        channelUrl:str              = 'https://www.youtube.com' + channelUrlFragment

        views:str                   = tryGetMultiKey(data, "0", "exactViews", "approxViews")
        viewsNum:int                = getApproximateNum(views)
        likes:str                   = tryGetMultiKey(data, "0", "exactLikes", "approxLikes")
        likesNum:int                = getApproximateNum(likes)

        avatar:list[Thumbnail]      = [Thumbnail.fromData(datum) for datum in tryGet(data, 'avatar', [])]

        channelName:str             = tryGet(data, 'channelName')
        subscribers:str             = tryGet(data, 'subscribers', "0")

        return cls(description, title, views, viewsNum, likes, likesNum, channelName, channelUrlFragment, channelUrl, channelId, avatar, uploadedOn, subscribers)



# >Playlist Info< #
playlistInfoScrapeFmt = \
    ScrapeNth("metadata", [
        ScrapeNth("title", [], rename = "title"),
        ScrapeNth("description", [],rename = "description", optional=True),
    ], collapse = True)

@dataclass
class PlaylistInfo:
    title:str
    description:str

    @classmethod
    def fromData(cls, data:dict) -> 'PlaylistInfo':
        title:str                   = tryGet(data, 'title')
        description:str             = tryGet(data, 'description')
        return cls(title, description)
    
    def __repr__(self):
        return f'{self.title}\n{self.description}\n'

    def __str__(self):
        return self.__repr__()


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
    channelId:str
    avatar:list[Thumbnail]

    @classmethod
    def fromData(cls, data:dict) -> Union['Upload', None]:
        try:
            videoId:str                 = data['videoId']
            uploadedOn:str              = data['uploadedOn']
        except KeyError as e:
            if cfg.testing:
                raise Exception(f'Missing Required Key "{e.args[0]}"\nFrom Data: {data}')
            cfg.logger.debug(f'In {cls.__name__}.fromData(), Data is Missing Required Key "{e.args[0]}"')
            return None

        url:str                     = 'https://www.youtube.com/watch?v=' + videoId
        unixTime:int                = approxTimeToUnix(currentTime, uploadedOn)
        thumbnails:list[Thumbnail]  = [Thumbnail.fromData(datum) for datum in tryGet(data, 'thumbnails', [])]
        views:str                   = tryGet(data, 'views')
        duration:str                = tryGet(data, 'duration')
        title:str                   = tryGet(data, 'title')

        # the following are added by subbox
        channelName:str = ''
        channelUrl:str = ''
        channelId:str = ''
        avatar:list[Thumbnail] = list()
        return cls(videoId, url, unixTime, thumbnails, uploadedOn, views, duration, title, channelName, channelUrl, channelId, avatar)
    
    def __repr__(self):
        return f'{self.title}\n     > {self.channelName} | {self.duration} | {self.uploadedOn} | {self.views}\n'

    def __str__(self):
        return self.__repr__()



# > Channel Playlists < #
channelPlaylistsApiUrl = '/youtubei/v1/browse'

channelPlaylistScrapeFmt = ScrapeAll("gridPlaylistRenderer", [
        ScrapeNth("title",[
            ScrapeAll("text",[], collapse=True),
        ], rename = "playlistTitle"),
        ScrapeNth("thumbnails",[], rename = 'playlistThumbnails'),
        ScrapeNth("playlistId",[]),
        ScrapeNth("videoCountText",[
            ScrapeAll("text",[], collapse=True),
        ], rename = "videoCount"),
    ], collapse = True)

@dataclass
class ChannelPlaylist:
    playlistTitle:str
    playlistThumbnails:list[Thumbnail]
    playlistId:str
    playlistUrl:str
    videoCount:str

    @classmethod
    def fromData(cls, data:dict) -> Union['ChannelPlaylist', None]:
        try:
            playlistId:str = data['playlistId']
        except KeyError as e:
            if cfg.testing:
                raise Exception(f'Missing Required Key "{e.args[0]}"\nFrom Data: {data}')
            cfg.logger.debug(f'In {cls.__name__}.fromData(), Data is Missing Required Key "{e.args[0]}"')
            return None

        playlistTitle:str = "".join(tryGet(data, 'playlistTitle', []))
        playlistThumbnails:list[Thumbnail]        = [Thumbnail.fromData(datum) for datum in tryGet(data, 'playlistThumbnails', [])]
        playlistUrl:str = "https://www.youtube.com/playlist?list=" + playlistId
        videoCount:str = "".join(tryGet(data, 'videoCount', []))

        return cls(playlistTitle, playlistThumbnails, playlistId, playlistUrl, videoCount)


# >Playlist Video< #
playlistVideosApiUrl = '/youtubei/v1/browse'

playlistVideosScrapeFmt = \
    ScrapeAll("playlistVideoRenderer", [
        *_uploadAndRelatedFmt("text", "lengthText", includePublishedTime = False, includeViewCount = False), 
        ScrapeNth("shortBylineText", [
            ScrapeNth("text", [], collapse = True),
        ], rename = "channelName"),
        ScrapeNth("shortBylineText", [
            ScrapeNth("url", [], collapse = True)
        ],rename = "channelUrlFragment"),
    ], collapse = True)

@dataclass
class PlaylistVideo:
    videoId:str
    url:str
    thumbnails:list[Thumbnail]
    duration:str
    title:str

    channelName:str
    channelUrlFragment:str
    channelUrl:str

    @classmethod
    def fromData(cls, data:dict) -> Union['PlaylistVideo', None]:
        try:
            videoId:str                 = data['videoId']
            channelUrlFragment:str      = data["channelUrlFragment"]
        except KeyError as e:
            if cfg.testing:
                raise Exception(f'Missing Required Key "{e.args[0]}"\nFrom Data: {data}')
            cfg.logger.debug(f'In {cls.__name__}.fromData(), Data is Missing Required Key "{e.args[0]}"')
            return None

        url:str                     = 'https://www.youtube.com/watch?v=' + videoId
        thumbnails:list[Thumbnail]  = [Thumbnail.fromData(datum) for datum in tryGet(data, 'thumbnails', [])]
        duration:str                = tryGet(data, 'duration')
        title:str                   = tryGet(data, 'title')

        channelName:str = tryGet(data, "channelName")
        channelUrl:str = 'https://www.youtube.com' + channelUrlFragment


        return cls(videoId, url, thumbnails, duration, title, channelName, channelUrlFragment, channelUrl)
    
    def __repr__(self):
        return f'{self.title}\n     > {self.channelName} | {self.duration} \n'

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
    def fromData(cls, data) -> 'Comment':
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
        ],rename = "channelUrlFragment"),
        ScrapeNth("channelThumbnail",[
            ScrapeNth("thumbnails",[], collapse=True),
        ], rename = "avatar"),

    ], collapse = True)

@dataclass
class RelatedVideo:
    videoId:str
    url:str
    thumbnails:list[Thumbnail]
    uploadedOn:str
    views:str
    duration:str
    title:str

    channelName:str
    channelUrlFragment:str
    channelUrl:str
    avatar:list[Thumbnail]

    @classmethod
    def fromData(cls, data:dict) -> Union['RelatedVideo', None]:
        try:
            videoId:str                 = data['videoId']
            channelUrlFragment:str      = data["channelUrlFragment"]
        except KeyError as e:
            if cfg.testing:
                raise Exception(f'Missing Required Key "{e.args[0]}"\nFrom Data: {data}')
            cfg.logger.debug(f'In {cls.__name__}.fromData(), Data is Missing Required Key "{e.args[0]}"')
            return None

        uploadedOn:str              = tryGet(data, 'uploadedOn')
        url:str                     = 'https://www.youtube.com/watch?v=' + videoId
        thumbnails:list[Thumbnail]  = [Thumbnail.fromData(datum) for datum in tryGet(data, 'thumbnails', [])]
        views:str                   = tryGet(data, 'views')
        duration:str                = tryGet(data, 'duration')
        title:str                   = tryGet(data, 'title')

        channelName:str = tryGet(data, "channelName")
        channelUrl:str = 'https://www.youtube.com' + channelUrlFragment

        avatar:list[Thumbnail]  = [Thumbnail.fromData(datum) for datum in tryGet(data, 'avatar', [])]

        return cls(videoId, url, thumbnails, uploadedOn, views, duration, title, channelName, channelUrlFragment, channelUrl, avatar)
    
    def __repr__(self):
        return f'{self.title}\n     > {self.channelName} | {self.duration} | {self.uploadedOn} | {self.views}\n'

    def __str__(self):
        return self.__repr__()



# >Search< #
searchUrl = "https://www.youtube.com/results?search_query="
searchApiUrl = '/youtubei/v1/search'
searchFilterSelectedStatus = "FILTER_STATUS_SELECTED"
searchFilterDisabledStatus = "FILTER_STATUS_DISABLED"


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
                    ScrapeNth("status", [], optional = True)

                ],  collapse=True),
            ]),
    ], collapse= True)

@dataclass
class SearchFilter:
    label:str
    # will be empty if selected
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
        filterData = tryGet(data, 'filters', [])

        filters = []
        for f in filterData:
            try:
                label = f['label']
                if 'status' in f:
                    if f['status'] == searchFilterDisabledStatus:
                        continue
                    selected = f['status'] == searchFilterSelectedStatus
                else:
                    selected = False

                # some selections have no url because they cannot be toggled off (ie sort by section)
                if 'searchUrlFragment' not in f and selected:
                    continue

                _searchUrlFragment = f['searchUrlFragment']

                searchUrlFragmentList = _searchUrlFragment.split("search_query=", maxsplit = 1)
                if len(searchUrlFragmentList) == 1:
                    searchUrlFragment = searchUrlFragmentList[0]
                else:
                    searchUrlFragment = searchUrlFragmentList[1]


            except KeyError as e:
                if cfg.testing:
                    raise Exception(f'Missing Required Key "{e.args[0]}"\nFrom Data: {data}')
                cfg.logger.debug(f'In {cls.__name__}.fromData(), Data is Missing Required Key "{e.args[0]}"')
                continue


            filters.append(SearchFilter(label, searchUrlFragment, selected))

        return cls(searchType, filters)

    def __len__(self):
        return len(self.filters)

    def __repr__(self):
        return self.searchType

    def __str__(self):
        return self.__repr__()



searchScrapeFmt = \
            ScrapeAllUnion("", [

                ScrapeAllUnionNode("channelRenderer", [

                    ScrapeNth("title",[
                        ScrapeNth("simpleText",[],collapse=True)
                    ], rename = 'channelName'),

                    ScrapeNth("browseEndpoint",[
                        ScrapeNth("canonicalBaseUrl", [],  collapse=True),
                    ], rename = 'channelUrlFragment'),

                    #ScrapeNth("thumbnails",[], rename = 'channelIcons'),

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

                    ScrapeNth("thumbnail",[
                        ScrapeNth("thumbnails",[], collapse=True),
                    ], rename = "avatar"),

                ], rename="channel"),


                ScrapeAllUnionNode("videoRenderer",[
                    ScrapeNth("title",[
                        ScrapeNth("text",[],collapse=True)
                    ]),

                    ScrapeNth("longBylineText",[
                        ScrapeNth("text", [],  collapse=True),
                    ], rename= "channelName"),

                    ScrapeNth("longBylineText",[
                        ScrapeNth("url", [], collapse=True)
                    ],rename="channelUrlFragment"),

                    ScrapeNth("videoId",[]),


                    ScrapeNth("thumbnail",[
                        ScrapeNth("thumbnails",[], collapse=True),
                    ], rename = "thumbnails"),

                    ScrapeNth("channelThumbnailSupportedRenderers",[
                        ScrapeNth("thumbnails",[], collapse=True),
                    ], rename = "avatar"),

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
    avatar:list[Thumbnail]
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
            channelUrlFragment = data["channelUrlFragment"]
        except KeyError as e:
            if cfg.testing:
                raise Exception(f'Missing Required Key "{e.args[0]}"\nFrom Data: {data}')
            cfg.logger.debug(f'In {cls.__name__}.fromData(), Data is Missing Required Key "{e.args[0]}"')
            return None

        url = 'https://www.youtube.com/watch?v=' + videoId
        channelUrl = 'https://www.youtube.com' + channelUrlFragment

        channelName                 = tryGet(data, "channelName")
        avatar:list[Thumbnail]      = [Thumbnail.fromData(datum) for datum in tryGet(data, 'avatar', [])]
        videoId                     = tryGet(data, "videoId")
        thumbnails:list[Thumbnail]  = [Thumbnail.fromData(datum) for datum in tryGet(data, 'thumbnails', [])]
        views                       = tryGet(data, "views")
        duration                    = tryGet(data, "duration")
        uploadedOn                  = tryGet(data, "uploadedOn")

        return cls(title, channelName, channelUrlFragment, channelUrl, avatar, videoId, url, thumbnails, views, duration, uploadedOn)

    def __repr__(self):
        return f'Video: {self.title}\n     > {self.channelName} | {self.duration} | {self.uploadedOn} | {self.views}\n'

    def __str__(self):
        return self.__repr__()

@dataclass
class SearchChannel:
    channelName:str
    channelUrlFragment:str
    channelUrl:str
    avatar:list[Thumbnail]
    channelDescription:str
    subscribers:str
    videoCount:str

    @classmethod
    def fromData(cls, data:dict) -> Union['SearchChannel', None]:
        try:
            channelName        = data['channelName']
            channelUrlFragment = data['channelUrlFragment']
        except KeyError as e:
            if cfg.testing:
                raise Exception(f'Missing Required Key "{e.args[0]}"\nFrom Data: {data}')
            cfg.logger.debug(f'In {cls.__name__}.fromData(), Data is Missing Required Key "{e.args[0]}"')
            return None

        channelUrl         = 'https://www.youtube.com' + channelUrlFragment
        avatar:list[Thumbnail]        = [Thumbnail.fromData(datum) for datum in tryGet(data, 'avatar', [])]
        channelDescription = tryGet(data, 'channelDescription')
        subscribers        = tryGet(data, 'subscribers')
        videoCount         = " ".join(tryGet(data, 'videoCount', []))

        return cls(channelName, channelUrlFragment, channelUrl, avatar, channelDescription, subscribers, videoCount)

    def __repr__(self):
        return f'Channel: {self.channelName}\n     > {self.subscribers} | {self.videoCount}\n'

    def __str__(self):
        return self.__repr__()
