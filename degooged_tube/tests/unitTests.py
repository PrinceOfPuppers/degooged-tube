import unittest
import inspect
import json

import degooged_tube.config as cfg
from degooged_tube.ytApiHacking.jsonScraping import scrapeJsonTree, ScrapeNode, ScrapeNum

def logName(testInstance, frame):
    assert frame is not None
    name = frame.f_code.co_name
    cfg.logger.info(f"Running {testInstance.__class__.__name__}: {name}")

def test_scrapeJsonTreeHelper(jsonName, fmt):
    with open(f"{cfg.testJsonPath}/{jsonName}") as  f:
        j = json.load(f)
        return scrapeJsonTree(j, fmt)

class test_scrapeJsonTree(unittest.TestCase):
    def test_handmade_1(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
              ScrapeNode("greetings", ScrapeNum.All,[
                  ScrapeNode("hi", ScrapeNum.First,[
                      ScrapeNode("name", ScrapeNum.All,[])
                  ]),
              ])

        try:
            answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt)
        except KeyError:
            self.fail("Scrape Json Tree Missed Key")

        solution = {'greetings': [{'hi': {'name': ['alice', 'bob', 'carol', 'dave']}}, {'hi': {'name': []}}]}


        self.assertEqual ( 
            answer, solution
        )


    def test_handmade_2(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
              ScrapeNode("greetings", ScrapeNum.All,[
                  ScrapeNode("hi", ScrapeNum.First,[
                      ScrapeNode("name", ScrapeNum.All,[])
                  ]),
              ], collapse = True)
        try:
            answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt)
        except KeyError:
            self.fail("Scrape Json Tree Missed Key")

        solution = [{'hi': {'name': ['alice', 'bob', 'carol', 'dave']}}, {'hi': {'name': []}}]

        self.assertEqual ( answer, solution )


    def test_handmade_3(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
              ScrapeNode("greetings", ScrapeNum.All,[
                  ScrapeNode("hi", ScrapeNum.First,[
                      ScrapeNode("name", ScrapeNum.All,[], collapse = True)
                  ]),
              ], collapse = True)

        try:
            answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt)
        except KeyError:
            self.fail("Scrape Json Tree Missed Key")

        solution = [{'hi': ['alice', 'bob', 'carol', 'dave']}, {'hi': []}]
        self.assertEqual ( answer, solution )

    def test_handmade_4(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
              ScrapeNode("greetings", ScrapeNum.All,[
                  ScrapeNode("hi", ScrapeNum.First,[
                      ScrapeNode("name", ScrapeNum.All,[], collapse = True)
                  ], collapse = True),
              ])

        try:
            answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt)
        except KeyError:
            self.fail("Scrape Json Tree Missed Key")

        solution = {'greetings': [['alice', 'bob', 'carol', 'dave'],[]]}
        self.assertEqual ( answer, solution )


    def test_handmade_5(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
              ScrapeNode("greetings", ScrapeNum.All,[
                  ScrapeNode("hi", ScrapeNum.First,[
                      ScrapeNode("name", ScrapeNum.All,[], collapse = True)
                  ], collapse = True),
              ], collapse = True)

        try:
            answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt)
        except KeyError:
            self.fail("Scrape Json Tree Missed Key")

        solution = [['alice', 'bob', 'carol', 'dave'],[]]
        self.assertEqual ( answer, solution )


    def test_handmade_6(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
              ScrapeNode("greetings", ScrapeNum.All,[
                  ScrapeNode("hi", ScrapeNum.First,[
                      ScrapeNode("name", ScrapeNum.All,[], collapse = True)
                  ], collapse = True),
              ], collapse = True)

        try:
            answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt)
        except KeyError:
            self.fail("Scrape Json Tree Missed Key")

        solution = [['alice', 'bob', 'carol', 'dave'],[]]
        self.assertEqual ( answer, solution )


    def test_handmade_7(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
              ScrapeNode("greetings", ScrapeNum.All,[
                  ScrapeNode("hi", ScrapeNum.First,[
                      ScrapeNode("coolness", ScrapeNum.All,[], collapse = True)
                  ], collapse = True),
              ], collapse = True)

        try:
            answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt)
        except KeyError:
            self.fail("Scrape Json Tree Missed Key")

        solution = [['megaRad', 11, ['super', 'duper', 'cool']],[]]
        self.assertEqual ( answer, solution )


    def test_handmade_8(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
              ScrapeNode("greetings", ScrapeNum.All,[
                  ScrapeNode("hi", ScrapeNum.First,[], collapse = True),
              ], collapse = True)

        solution = [
            [
                { "name": "alice", "favColor": "blue", "coolness": "megaRad"},
                { "name": "bob", "favColor": "green", "coolness": 11 },
                { "name": "carol", "favColor": "purple", "coolness": ["super", "duper", "cool"] },
                { "name": "dave", "favColor": "purple" }
            ], 
                [1, 2, 3]
        ]

        try:
            answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt)
        except KeyError:
            self.fail("Scrape Json Tree Missed Key")

        self.assertEqual( answer, solution )


    def test_handmade_9(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
              ScrapeNode("greetings", ScrapeNum.Longest,[
                  ScrapeNode("hi", ScrapeNum.First,[], collapse = True),
              ], collapse = True)

        solution = [
                { "name": "alice", "favColor": "blue", "coolness": "megaRad"},
                { "name": "bob", "favColor": "green", "coolness": 11 },
                { "name": "carol", "favColor": "purple", "coolness": ["super", "duper", "cool"] },
                { "name": "dave", "favColor": "purple" }
        ]

        try:
            answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt)
        except KeyError:
            self.fail("Scrape Json Tree Missed Key")

        self.assertEqual(answer, solution)


    def test_handmade_10(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
              ScrapeNode("greetings", ScrapeNum.Longest,[
                  ScrapeNode("hi", ScrapeNum.First,[]),
              ], collapse = True)

        solution = \
            {
                "hi" : [
                    { "name": "alice", "favColor": "blue", "coolness": "megaRad"},
                    { "name": "bob", "favColor": "green", "coolness": 11 },
                    { "name": "carol", "favColor": "purple", "coolness": ["super", "duper", "cool"] },
                    { "name": "dave", "favColor": "purple" }
                ]
            }

        try:
            answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt)
        except KeyError:
            self.fail("Scrape Json Tree Missed Key")

        self.assertEqual(answer, solution)


    def test_handmade_11(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
              ScrapeNode("greetings", ScrapeNum.Longest,[
                  ScrapeNode("hi", ScrapeNum.First,[
                      ScrapeNode("name", ScrapeNum.All,[], collapse = True)
                  ]),
              ], collapse = True)

        solution = { "hi" : ['alice', 'bob', 'carol', 'dave'] }

        try:
            answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt)
        except KeyError:
            self.fail("Scrape Json Tree Missed Key")

        self.assertEqual(answer, solution)


    def test_handmade_12(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
              ScrapeNode("greetings", ScrapeNum.Longest,[
                  ScrapeNode("hi", ScrapeNum.Longest,[
                      ScrapeNode("name", ScrapeNum.All,[], collapse = True)
                  ]),
              ], collapse = True)

        solution = { "hi" : ['alice', 'bob', 'carol', 'dave'] }

        try:
            answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt)
        except KeyError:
            self.fail("Scrape Json Tree Missed Key")

        self.assertEqual(answer, solution)


    def test_example_1(self):
        channelInfoScrapeFmt = \
            ScrapeNode("header", ScrapeNum.First,[
                ScrapeNode("title", ScrapeNum.First,[], rename='name'),
                ScrapeNode("canonicalBaseUrl", ScrapeNum.First,[], rename='baseUrl'),
                ScrapeNode("avatar", ScrapeNum.First,[
                    ScrapeNode("thumbnails", ScrapeNum.All,[], collapse=True),
                ], rename='baseUrl'),
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

        solution = \
            json.loads(
                    '{"name": "Matt McMuscles", "baseUrl": [[{"url": "https://yt3.ggpht.com/ytc/AKedOLQwUYQ7QO_7ZseJMxK42l46IjHEdd3DML3L-7lYXQ=s48-c-k'
                    '-c0x00ffffff-no-rj", "width": 48, "height": 48}, {"url": "https://yt3.ggpht.com/ytc/AKedOLQwUYQ7QO_7ZseJMxK42l46IjHEdd3DML3L-7lYXQ'
                    '=s88-c-k-c0x00ffffff-no-rj", "width": 88, "height": 88}, {"url": "https://yt3.ggpht.com/ytc/AKedOLQwUYQ7QO_7ZseJMxK42l46IjHEdd3DML'
                    '3L-7lYXQ=s176-c-k-c0x00ffffff-no-rj", "width": 176, "height": 176}]], "banners": [[{"url": "https://yt3.ggpht.com/P4qklhp6Kp5h33yd'
                    'SmXpYWhFkvlVu7zCunBpXKyc8CwjuEVjjkx2wswBLyHtgaphowjz3tPt=w1060-fcrop64=1,00005a57ffffa5a8-k-c0xffffffff-no-nd-rj", "width": 1060,'
                    '"height": 175}, {"url": "https://yt3.ggpht.com/P4qklhp6Kp5h33ydSmXpYWhFkvlVu7zCunBpXKyc8CwjuEVjjkx2wswBLyHtgaphowjz3tPt=w1138-fcro'
                    'p64=1,00005a57ffffa5a8-k-c0xffffffff-no-nd-rj", "width": 1138, "height": 188}, {"url": "https://yt3.ggpht.com/P4qklhp6Kp5h33ydSmXp'
                    'YWhFkvlVu7zCunBpXKyc8CwjuEVjjkx2wswBLyHtgaphowjz3tPt=w1707-fcrop64=1,00005a57ffffa5a8-k-c0xffffffff-no-nd-rj", "width": 1707, "hei'
                    'ght": 283}, {"url": "https://yt3.ggpht.com/P4qklhp6Kp5h33ydSmXpYWhFkvlVu7zCunBpXKyc8CwjuEVjjkx2wswBLyHtgaphowjz3tPt=w2120-fcrop64='
                    '1,00005a57ffffa5a8-k-c0xffffffff-no-nd-rj", "width": 2120, "height": 351}, {"url": "https://yt3.ggpht.com/P4qklhp6Kp5h33ydSmXpYWhF'
                    'kvlVu7zCunBpXKyc8CwjuEVjjkx2wswBLyHtgaphowjz3tPt=w2276-fcrop64=1,00005a57ffffa5a8-k-c0xffffffff-no-nd-rj", "width": 2276, "height"'
                    ': 377}, {"url": "https://yt3.ggpht.com/P4qklhp6Kp5h33ydSmXpYWhFkvlVu7zCunBpXKyc8CwjuEVjjkx2wswBLyHtgaphowjz3tPt=w2560-fcrop64=1,00'
                    '005a57ffffa5a8-k-c0xffffffff-no-nd-rj", "width": 2560, "height": 424}]], "mobileBanners": [[{"url": "https://yt3.ggpht.com/P4qklhp'
                    '6Kp5h33ydSmXpYWhFkvlVu7zCunBpXKyc8CwjuEVjjkx2wswBLyHtgaphowjz3tPt=w320-fcrop64=1,32b75a57cd48a5a8-k-c0xffffffff-no-nd-rj", "width"'
                    ': 320, "height": 88}, {"url": "https://yt3.ggpht.com/P4qklhp6Kp5h33ydSmXpYWhFkvlVu7zCunBpXKyc8CwjuEVjjkx2wswBLyHtgaphowjz3tPt=w640'
                    '-fcrop64=1,32b75a57cd48a5a8-k-c0xffffffff-no-nd-rj", "width": 640, "height": 175}, {"url": "https://yt3.ggpht.com/P4qklhp6Kp5h33yd'
                    'SmXpYWhFkvlVu7zCunBpXKyc8CwjuEVjjkx2wswBLyHtgaphowjz3tPt=w960-fcrop64=1,32b75a57cd48a5a8-k-c0xffffffff-no-nd-rj", "width": 960, "h'
                    'eight": 263}, {"url": "https://yt3.ggpht.com/P4qklhp6Kp5h33ydSmXpYWhFkvlVu7zCunBpXKyc8CwjuEVjjkx2wswBLyHtgaphowjz3tPt=w1280-fcrop6'
                    '4=1,32b75a57cd48a5a8-k-c0xffffffff-no-nd-rj", "width": 1280, "height": 351}, {"url": "https://yt3.ggpht.com/P4qklhp6Kp5h33ydSmXpYW'
                    'hFkvlVu7zCunBpXKyc8CwjuEVjjkx2wswBLyHtgaphowjz3tPt=w1440-fcrop64=1,32b75a57cd48a5a8-k-c0xffffffff-no-nd-rj", "width": 1440, "heigh'
                    't": 395}]], "subscribers": ["425K subscribers"]}'
            )

        try:
            answer = test_scrapeJsonTreeHelper("example.json", channelInfoScrapeFmt)
        except KeyError:
            self.fail("Scrape Json Tree Missed Key")


        self.assertEqual(answer, solution)
