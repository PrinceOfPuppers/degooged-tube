import unittest
import inspect
import json

import degooged_tube.config as cfg
from degooged_tube.ytapiHacking.jsonScraping import scrapeJsonTree, ScrapeNode, ScrapeNum

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


        self.assertEqual ( 
                test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt), 
                {'greetings': [{'hi': {'name': ['alice', 'bob', 'carol', 'dave']}}, {'hi': {'name': []}}]}
        )

    def test_handmade_2(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
              ScrapeNode("greetings", ScrapeNum.All,[
                  ScrapeNode("hi", ScrapeNum.First,[
                      ScrapeNode("name", ScrapeNum.All,[])
                  ]),
              ], collapse = True)

        self.assertEqual ( 
                test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt),
                [{'hi': {'name': ['alice', 'bob', 'carol', 'dave']}}, {'hi': {'name': []}}]
        )


    def test_handmade_3(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
              ScrapeNode("greetings", ScrapeNum.All,[
                  ScrapeNode("hi", ScrapeNum.First,[
                      ScrapeNode("name", ScrapeNum.All,[], collapse = True)
                  ]),
              ], collapse = True)

        self.assertEqual ( 
                test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt),
                [{'hi': ['alice', 'bob', 'carol', 'dave']}, {'hi': []}]
        )

    def test_handmade_4(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
              ScrapeNode("greetings", ScrapeNum.All,[
                  ScrapeNode("hi", ScrapeNum.First,[
                      ScrapeNode("name", ScrapeNum.All,[], collapse = True)
                  ], collapse = True),
              ])

        self.assertEqual ( 
                test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt),
                {'greetings': [['alice', 'bob', 'carol', 'dave'],[]]}
        )

    def test_handmade_5(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
              ScrapeNode("greetings", ScrapeNum.All,[
                  ScrapeNode("hi", ScrapeNum.First,[
                      ScrapeNode("name", ScrapeNum.All,[], collapse = True)
                  ], collapse = True),
              ], collapse = True)

        self.assertEqual ( 
                test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt),
                [['alice', 'bob', 'carol', 'dave'],[]]
        )

    def test_handmade_6(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
              ScrapeNode("greetings", ScrapeNum.All,[
                  ScrapeNode("hi", ScrapeNum.First,[
                      ScrapeNode("name", ScrapeNum.All,[], collapse = True)
                  ], collapse = True),
              ], collapse = True)

        self.assertEqual ( 
                test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt),
                [['alice', 'bob', 'carol', 'dave'],[]]
        )

    def test_handmade_7(self):
        logName(self, inspect.currentframe())

        uploadScrapeFmt = \
              ScrapeNode("greetings", ScrapeNum.All,[
                  ScrapeNode("hi", ScrapeNum.First,[
                      ScrapeNode("coolness", ScrapeNum.All,[], collapse = True)
                  ], collapse = True),
              ], collapse = True)

        self.assertEqual ( 
                test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt),
                [['megaRad', 11, ['super', 'duper', 'cool']],[]]
        )

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

        answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt)
        self.assertEqual(answer, solution)

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

        answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt)
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

        answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt)
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

        answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt)
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

        answer = test_scrapeJsonTreeHelper("random.json", uploadScrapeFmt)
        self.assertEqual(answer, solution)

