import requests
import re
import json
from enum import Enum
from typing import List, Union, Tuple
from dataclasses import dataclass

import degooged_tube.config as cfg


apiKeyRe = re.compile(r'[\'\"]INNERTUBE_API_KEY[\'\"]:[\'\"](.*?)[\'\"]')
continuationTokenRe = re.compile(r'[\'\"]token[\'\"]\s?:\s?[\'\"](.*?)[\'\"]')
clientVersionRe = re.compile(r'[\'\"]cver[\'\"]: [\'|\"](.*?)[\'\"]')
ytInitalDataRe = re.compile(r"ytInitialData = (\{.*?\});</script>")


def scrapeJson(j, desiredKey: str, results:List):
    if isinstance(j,List):
        for value in j:
            if isinstance(value,List) or isinstance(value,dict):
                scrapeJson(value, desiredKey, results)
        return

    if isinstance(j, dict):
        for key,value in j.items():
            if key == desiredKey:
                results.append(value)
            elif isinstance(value, dict) or isinstance(value, List):
                scrapeJson(value, desiredKey, results)
        return

def scrapeFirstJson(j, desiredKey: str):
    if isinstance(j,List):
        for value in j:
            if isinstance(value,List) or isinstance(value,dict):
                res = scrapeFirstJson(value, desiredKey)
                if res is not None:
                    return res
        return None

    if isinstance(j, dict):
        for key,value in j.items():
            if key == desiredKey:
                return value
            elif isinstance(value, dict) or isinstance(value, List):
                res = scrapeFirstJson(value, desiredKey)
                if res is not None:
                    return res
        return None

    return None



class ScrapeNum(Enum):
    First = 1
    All = 2

@dataclass()
class ScrapeNode:
    key: str
    scrapeNum: ScrapeNum
    children: list

    collapse: bool = False

def _put(src, dest: Union[list, dict], key: Union[str,None] = None):
    if type(dest) is list:
        dest.append(src)
        return
    elif type(dest) is dict:
        if key == None:
            cfg.logger.error("Key Required")
            return

        dest[key] = src

def scrapeJsonTree(j, base: ScrapeNode, result: Union[dict, list], parentKey: str = None):

    # if parent key is provided, put data under parents key
    if parentKey == None:
        putKey = base.key
    else:
        putKey = parentKey


    if base.scrapeNum == ScrapeNum.All:
        data = []
        scrapeJson(j, base.key, data)

        if len(base.children) == 0:
            _put(data, result, putKey)
            return

        x = []
        for datum in data:
            y = {}
            for child in base.children:
                if child.collapse:
                    scrapeJsonTree(datum, child, x, putKey)
                else:
                    scrapeJsonTree(datum, child, y)
            x.append(y)
        _put(x, result, putKey)

    else: 
        data = scrapeFirstJson(j, base.key)

        if data is None:
            cfg.logger.error(f"Missing Field in JSON: {base.key}")
            return

        if len(base.children) == 0:
            _put(data, result, putKey)
            return

        for child in base.children:
            if child.collapse:
                scrapeJsonTree(data, child, result, putKey)
            else:
                x = {}
                scrapeJsonTree(data, child, x)
                _put(x, result, putKey)
    


@dataclass()
class YoutubeApiData:
    url: str
    continuationUrlFragment: str
    key: str
    continuationToken: str
    clientVersion: str
    endOfData:bool

    initalData: Union[dict, None] = None # used to store elements provided on first page load, set to none after first getNext


    @classmethod
    def fromUrl(cls, url:str, continuationUrlFragment: str, getDataInScript = True) -> Union['YoutubeApiData', None]:
        r=requests.get(url)

        x,y,z = apiKeyRe.search(r.text), continuationTokenRe.search(r.text), clientVersionRe.search(r.text)


        if not x:
            cfg.logger.error("Unable to Find INNERTUBE_API_KEY")
            return None

        if not y:
            cfg.logger.error("Unable to Find Continuation Token")
            return None

        if not z:
            cfg.logger.error("Unable to Find Youtube Client Version")
            return None

        key = x.group(1)
        continuationToken = y.group(1)
        clientVersion = z.group(1)

        if getDataInScript:
            a = ytInitalDataRe.search(r.text)
            if not a:
                cfg.logger.error("Unable to Find ScriptData")
                return None
            b = a.group(1)
            initalData = json.loads(b)
            return cls(url, continuationUrlFragment, key, continuationToken, clientVersion,False, initalData)

        return cls(url, continuationUrlFragment, key, continuationToken, clientVersion,False)


    def getNext(self) -> Union[dict, None]:

        # gets element that was sent on page load
        if self.initalData:
            data = self.initalData
            self.initalData = None
            return data

        if self.endOfData:
            return None
        requestData = '''{
            "context": {
                "adSignalsInfo": {
                },
                "clickTracking": {
                },
                "client": {
                    "clientName": "WEB",
                    "clientVersion": "'''+self.clientVersion+'''",
                },
                "request": {
                },
                "user": {
                }
            },
            "continuation": "'''+self.continuationToken+'''"
        }'''
        
        reqUrl = f'https://www.youtube.com/youtubei/v1/{self.continuationUrlFragment}?key={self.key}'
        b = requests.post(reqUrl, data=requestData)
        cfg.logger.debug(f"Sent Post Request to: {reqUrl} \nStatus {b.status_code} {b.reason}")

        if b.status_code != 200:
            cfg.logger.error(f"Error Sending Post Request to: {reqUrl} \nStatus {b.status_code} {b.reason}")
            return None
        
        x = continuationTokenRe.search(b.text)

        if not x:
            self.endOfData = True
            cfg.logger.debug(f"Reached End of Continuation Chain, Yeilding Last Result")
        else:
            self.continuationToken = x.group(1)


        data:dict = json.loads(b.text)
        return data
