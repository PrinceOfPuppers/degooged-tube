from unittest import TestCase
import inspect
import json
import degooged_tube.config as cfg
from degooged_tube.ytApiHacking.jsonScraping import scrapeJsonTree, ScrapeAll, ScrapeNth, ScrapeLongest, ScrapeUnion, ScrapeAllUnion, ScrapeAllUnionNode, ScrapeError
from degooged_tube.ytApiHacking.helpers import getApproximateNum

def logName(testInstance, frame):
    assert frame is not None
    name = frame.f_code.co_name
    cfg.logger.info(f"Running {testInstance.__class__.__name__}: {name}")

def test_scrapeJsonTreeHelper(jsonName, fmt, percentRequiredKeys = None):
    with open(f"{cfg.testJsonPath}/{jsonName}") as  f:
        j = json.load(f)
        return scrapeJsonTree(j, fmt, truncateThreashold = percentRequiredKeys)

class test_scrapeJsonTree(TestCase):
    def test_handmade_1(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
              ScrapeAll("greetings",[
                  ScrapeNth("hi",[
                      ScrapeAll("name",[])
                  ]),
              ])

        try:
            answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt)
        except KeyError:
            self.fail("Scrape Json Tree Missed Key")

        solution = {'greetings': [{'hi': {'name': ['alice', 'bob', 'carol', 'dave']}}]}


        self.assertEqual ( 
            answer, solution
        )


    def test_handmade_2(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
              ScrapeAll("greetings",[
                  ScrapeNth("hi",[
                      ScrapeAll("name",[])
                  ]),
              ], collapse = True)
        try:
            answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt)
        except KeyError:
            self.fail("Scrape Json Tree Missed Key")

        solution = [{'hi': {'name': ['alice', 'bob', 'carol', 'dave']}}]

        self.assertEqual ( answer, solution )


    def test_handmade_3(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
              ScrapeAll("greetings",[
                  ScrapeNth("hi",[
                      ScrapeAll("name",[], collapse = True)
                  ]),
              ], collapse = True)

        try:
            answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt)
        except KeyError:
            self.fail("Scrape Json Tree Missed Key")

        solution = [{'hi': ['alice', 'bob', 'carol', 'dave']}]
        self.assertEqual ( answer, solution )

    def test_handmade_4(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
              ScrapeAll("greetings",[
                  ScrapeNth("hi",[
                      ScrapeAll("name",[], collapse = True)
                  ], collapse = True),
              ])

        try:
            answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt)
        except KeyError:
            self.fail("Scrape Json Tree Missed Key")

        solution = {'greetings': [['alice', 'bob', 'carol', 'dave']]}
        self.assertEqual ( answer, solution )


    def test_handmade_5(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
              ScrapeAll("greetings",[
                  ScrapeNth("hi",[
                      ScrapeAll("name",[], collapse = True)
                  ], collapse = True),
              ], collapse = True)

        try:
            answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt)
        except KeyError:
            self.fail("Scrape Json Tree Missed Key")

        solution = [['alice', 'bob', 'carol', 'dave']]
        self.assertEqual ( answer, solution )


    def test_handmade_6(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
              ScrapeAll("greetings",[
                  ScrapeNth("hi",[
                      ScrapeAll("name",[], collapse = True)
                  ], collapse = True),
              ], collapse = True)

        try:
            answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt)
        except KeyError:
            self.fail("Scrape Json Tree Missed Key")

        solution = [['alice', 'bob', 'carol', 'dave']]
        self.assertEqual ( answer, solution )


    def test_handmade_7(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
              ScrapeAll("greetings",[
                  ScrapeNth("hi",[
                      ScrapeAll("coolness",[], collapse = True)
                  ], collapse = True),
              ], collapse = True)

        try:
            answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt)
        except KeyError:
            self.fail("Scrape Json Tree Missed Key")

        solution = [['megaRad', 11, ['super', 'duper', 'cool']]]
        self.assertEqual ( answer, solution )


    def test_handmade_8(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
              ScrapeAll("greetings",[
                  ScrapeNth("hi",[], collapse = True),
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
              ScrapeLongest("greetings",[
                  ScrapeNth("hi",[], collapse = True),
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
              ScrapeLongest("greetings",[
                  ScrapeNth("hi",[]),
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
              ScrapeLongest("greetings",[
                  ScrapeNth("hi",[
                      ScrapeAll("name",[], collapse = True)
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
              ScrapeLongest("greetings",[
                  ScrapeLongest("hi",[
                      ScrapeAll("name",[], collapse = True)
                  ]),
              ], collapse = True)

        solution = { "hi" : ['alice', 'bob', 'carol', 'dave'] }

        try:
            answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt)
        except KeyError:
            self.fail("Scrape Json Tree Missed Key")

        self.assertEqual(answer, solution)

    def test_handmade_13(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
                  ScrapeNth("colors",[])

        solution = {"colors": ["purple", "green" ,"red" ]}

        try:
            answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt)
        except KeyError:
            self.fail("Scrape Json Tree Missed Key")

        self.assertEqual(answer, solution)

    def test_handmade_14(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
              ScrapeLongest("greetings",[
                  ScrapeNth("hi",[]),
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

    def test_handmade_15(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
              [
                  ScrapeNth("nested",[
                          ScrapeAll("name",[], rename="names")
                  ], collapse = True ),

                  ScrapeNth("colors",[]),
              ]

        solution = [ {"names" : ['partner', 'alice', 'bob', 'carol', 'dave']},  {"colors": ["purple", "green" ,"red" ]} ]

        try:
            answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt)
        except KeyError:
            self.fail("Scrape Json Tree Missed Key")

        self.assertEqual(answer, solution)

    def test_handmade_16(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
                  ScrapeLongest("beverages",[
                          ScrapeNth("coffee",[], rename = "Bean Juice"),
                          ScrapeNth("kvass",[], rename ="Bread Blessing")
                  ], collapse = True )

        solution = {"Bean Juice": "omegaGood", "Bread Blessing": "megaGood"}

        answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt)

        self.assertEqual(answer, solution)

    def test_handmade_17(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
              ScrapeNth("greetings",[
                  ScrapeNth("hi",[
                      ScrapeAll("name",[], rename="names"),
                      ScrapeAll("favColor",[], rename="favColors")
                  ], collapse=True),
              ], collapse = True)

        solution = \
            { 
                "names": ["alice", "bob", "carol", "dave"], 
                "favColors": ["blue", "green", "purple", "purple" ]
            }

        answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt)

        self.assertEqual(answer, solution)

    def test_someMissing_1(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
              [
                  ScrapeNth("nested",[
                      ScrapeAll("name",[], rename="names")
                  ], collapse = True ),

                  ScrapeNth("colors",[]),

                  ScrapeNth("should_be_missing",[])
              ]

        try:
            _ = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt, 1.0)
        except ScrapeError:
            pass
        else:
            self.fail("ScrapeJsonTree Should have Raised Excpetion")

        try:
            answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt, 0.5)
        except ScrapeError:
            self.fail("ScrapeJsonTree Should Not Have Raised Excpetion")

        solution = [ {"names" : ['partner', 'alice', 'bob', 'carol', 'dave']},  {"colors": ["purple", "green" ,"red" ]} ]
        self.assertEqual(answer, solution)


    def test_example_1(self):
        logName(self, inspect.currentframe())
        channelInfoScrapeFmt = \
            ScrapeNth("header",[

                ScrapeNth("title",[], rename='name'),

                ScrapeNth("canonicalBaseUrl",[], rename='baseUrl'),
                ScrapeNth("avatar",[
                    ScrapeAll("thumbnails",[], collapse=True),
                ], rename='baseUrl'),

                ScrapeNth("banner",[
                    ScrapeAll("thumbnails",[], collapse=True),
                ], rename='banners'),

                ScrapeNth("mobileBanner",[
                    ScrapeAll("thumbnails",[], collapse=True),
                ], rename='mobileBanners'),

                ScrapeNth("subscriberCountText",[
                    ScrapeAll("simpleText",[], collapse=True),
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

    def test_handmade_badFmt_1(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
              ScrapeLongest("greetings",[
                  ScrapeLongest("hi",[
                      ScrapeAll("name",[], collapse = True)
                  ]),
              ], collapse = True)

        solution = { "hi" : ['alice', 'bob', 'carol', 'dave'] }

        try:
            answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt)
        except KeyError:
            self.fail("Scrape Json Tree Missed Key")

        self.assertEqual(answer, solution)

    def test_handmade_ScrapeUnion_1(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
            ScrapeUnion([
              ScrapeAll("hello",[]),
              ScrapeAll("howdy",[]),
            ])

        solution = \
            { 
                "hello": ["there", "boio"], 
            }

        answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt, 1.0)

        self.assertEqual(answer, solution)

    def test_handmade_ScrapeUnion_2(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
            ScrapeUnion([
              ScrapeAll("hello",[], collapse = True),
              ScrapeAll("howdy",[]),
            ])

        solution = ["there", "boio"]

        answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt, 1.0)

        self.assertEqual(answer, solution)

    def test_handmade_ScrapeAllUnion_1(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
            ScrapeAllUnion("", [
              ScrapeAllUnionNode("hello",[], collapse = True),
              ScrapeAllUnionNode("howdy",[
                  ScrapeNth("name", [], collapse = True)
              ], collapse = True),
            ], collapse = True)

        solution = ["there", "partner", "boio"]

        answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt, 1.0)

        self.assertEqual(answer, solution)



class test_helpers(TestCase):
    def test_getApproxNum_1(self):
        logName(self, inspect.currentframe())
        x = "  100K views "
        val = getApproximateNum(x)
        self.assertEqual (100000, val)

    def test_getApproxNum_2(self):
        logName(self, inspect.currentframe())
        x = "1M Likes"
        val = getApproximateNum(x)
        self.assertEqual (1000000, val)

    def test_getApproxNum_3(self):
        logName(self, inspect.currentframe())
        x = "5 uploads"
        val = getApproximateNum(x)
        self.assertEqual (5, val)

    def test_getApproxNum_4(self):
        logName(self, inspect.currentframe())
        x = "11 "
        val = getApproximateNum(x)
        self.assertEqual (11, val)
