# degooged-tube

> An adless, accountless, trackerless youtube interface with a sub box
- [INSTALLATION](#INSTALLATION)
- [ABOUT](#ABOUT)
- [USAGE](#USAGE)
- [DEVLOPMENT](#DEVLOPMENT)
- [SCRAPING](#SCRAPING)
- [API](#API)



# INSTALLATION
Requires mpv for terminal playback

Install degooged-tube via pypi using pip:
``` 
pip install degooged-tube
```


# ABOUT
Allows for youtube to be used from a terminal with no ads, without an account account, and while maintaining subbox functionality. 

Can be embedded into other projects using the api in `degooged_tube/ytApiHacking/__init__.py`

All youtube api scraping is done internally, with the exception of getting the streaming link for videos, which is done with `yt-dlp`



# Usage
Launch in terminal with command
```
degooged-tube
```
Follow prompts to create a new 'user' (info is stored locally, has nothing to do with a youtube account), I recommend adding a few subs initally as it makes getting use to the cli easier.

### General Interface
CLI is interactive, options are displayed on the bottom of the screen and can be sepected by entering the letter in the brackets, IE w for `(w)atch`.

Some options IE `(w)atch` will show you a numbered list then prompt you for which number you want to watch, others IE `(p)revious/(n)ext page` will just preform the action.



# DEVLOPMENT
To build for devlopment run:
```
git clone https://github.com/PrinceOfPuppers/degooged-tube

cd degooged-tube

pip install -e .
```
This will build and install sync-dl in place, allowing you to work on the code without having to reinstall after changes.

### Automated Testing
```
python test.py [options]
```
Will run all unit and integration tests, options are -u and -i to only run the unit/integration tests respectively.



# SCRAPING
Youtube will sometimes change their api, most of the time this is not an issue as the scraping engine is robust, however sometimes scrapers will be broken, as such here is a guide on how they work and how to repair them

The configuration of youtube-api hacking exists in `degooged_tube/ytApiHacking/controlPanel.py`

### ScrapeJsonTree
The core of degooged-tube is a json scraping engine which is robust against chainging apis, and easily repairable in the event of a scraper breaking.

It works by defining nodes in a json tree down to the data you wish to collect, you can specify as many or as few nodes as is needed.

#### Examples
```
"greetings":{
    "hello": "there",
    "howdy": {"name": "partner"},
    "hi":[
        { 
            "name": "alice",
            "favColor": "blue",
            "coolness": "megaRad"
        },
        { 
            "name": "bob", 
            "favColor": "green",
            "coolness": 11
        },
        { 
            "name": "carol",
            "favColor": "purple",
            "coolness": ["super", "duper", "cool"]
        },
        { 
            "name": "dave",
            "favColor": "purple"
        }
    ]
}
```
Example Scrapers: 
- `ScrapeNth("howdy")` (N defaults to 1 or first) we would just get `{"howdy": {"name": "partner"}}`

- `ScrapeNth("howdy", collapse = True)` we would just get `{"name": "partner"}`, collapse just returns the data for a node, rather than key value pairs

- `ScrapeAll("name")` we would just get `{"name": ["partner", "alice", "bob", "carol", "dave"]}`

- `ScrapeNth("hi", [ScrapeNth("name" )])` we would get `{"hi": {"name": "alice"}}"` because we would first get `"hi"`, and then scrape for the first `"name"` in said data

- `ScrapeNth("hi", [ScrapeNth("name", collapse=True)])` we would get `{"hi": "alice"}"`, `"name"` has been collapsed

- `ScrapeNth("hi", [ScrapeNth("name"), ScrapeNth("favColor")])` we would get `{"hi": [{"name": "alice"}, {"favColor":"blue"}]}`

- `ScrapeAll("name", collapse=True, dataCondition=lambda data: data[1] = 'a')` we would get `['carol', 'dave']` as `dataCondition` filters all data which fail the condition

- `ScrapeUnion([ScrapeNth("missing key",[], collapse=True), ScrapeNth("hello",[], collapse = True)])` we would get `"there"`, however if `"missing key"` was present we would get the data for that instead

For more examples using all nodes and arguments, see `degooged_tube/ytApiHacking/controlPanel.py`.

For more involved examples of how this system is used in pratice, see `degooged_tube/tests/unitTests.py`.

#### Node Types
- `ScrapeNth`: \
Scrapes and returns the data for n'th occurance of the key

- `ScrapeAll`: \
Scrapes and returns the a list of data for all occurance of the key

- `ScrapeLongest`: \
Scrapes and returns the data with largest `len(data)` for all occurance of the key

- `ScrapeUnion([Node1, Node2, ...])`: \
Will scrape for each node and return the data first one which matches

- `ScrapeAllUnion`/`ScrapeAllUnionNode`: \
Used togeather as such: `ScrapeAllUnion([ScrapeAllUnionNode, ScrapeAllUnionNode, ...])`, will return a list containing all matches for any of the `ScrapeAllUnionNode`

- `ScrapeElement`: \
The generic type of any scrape node


# SANATIZATION
After scraping the data is passed into the `.fromData()` constructor of a dataclass (ie `VideoInfo.fromData()`), all of which are located in `degooged_tube/ytApiHacking/controlPanel.py` where it is sanitized and any missing data can be filled with placeholder data


# YOUTUBE-API-WRAPPERS 
There are 3 Objects which which wrap the youtube-api and allow for easy access to resources

#### YtInitalPage

Constructed using `YtInitalPage.fromUrl(url: str)` gets a page and parses it for containuation chains and inital data

The method `page.scrapeInitalData(dataFmt: Union[ScrapeElement, list[ScrapeElement]])` will run scrapeJsonTree on any inital data found and return it as a dict

#### YtApiList
Constructed from `YtInitalPage`, it behaves like a list and making calls to a continuation chain as items are indexed.

The continuation chain is decided using the apiUrl, and by duck-typing based on the scrapeFmt (following only chains which match the dataFmt).

Contains `YtContIter`, an iterator which wraps the continuation chains, deals the requests, as well as implements the aformentioned duck-typing


# DEGOOGED-TUBE-API
`degooged_tube/ytApiHacking/__init__.py` contains getter functions to return dataclasses, aswell as `YtApiLists` of dataclasses containing scraped data

pipeline under the hood (note this is not a callstack, for example processInfo is called in getter, its more a sequence diagram):
```
                                                                youtube-api
                                                                    ||
url/query -------------> getter --> YtInitalPage --+     +--> scrapeInitalData -------> scrapeJsonTree --> processInfo ---+---> fromData --> dataclass
   |                                               +-----+                                                                |
   +--> YtInitalPage --> getter -------------------+     +--> YtApiList/YtContIter ---> scrapeJsonTree --> onExtend ------+
                                                                    ||
                                                                youtube-api
```

Ledgend:
- `url/query`: \
url or search query

- `YtInitalPage`: \
created using `fromUrl()` 

- `getter`: \
functions in `degooged_tube/ytApiHacking/__init__.py` prepended by `get`

- `scrapeInitalData`: \
a method of `YtInitalPage` is passes the requsitie format to by getter

- `YtApiList\YtContIter`: \
`YtApiList` is instanceated by getter and passes the requsitie format to by getter, `YtContIter` in instanceated as a component of `YtApiList`

- `scrapeJsonTree`: \
uses the format on data requested from the youtube-api

- `processInfo`: \
the functions in `degooged_tube/ytApiHacking/__init__.py` called `process[BLANK]Info`, typically just calls `fromData` on the requisite dataclass

- `onExtend`: \
the functions in `degooged_tube/ytApiHacking/__init__.py` called `[BLANK]OnExtend`, typically just calls `fromData` on the requisite dataclass (can be overriden to inject data using `OnExtendKwargs` in a few cases)

- `fromData`: \
the constructors in `degooged_tube/ytApiHacking/controlPanel.py` which create a dataclass to hold the scraped data (ie `VideoInfo.fromData()`). they also santize and any replaces missing fields with placeholder data if possible
