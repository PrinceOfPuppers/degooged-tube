import requests
import json
from typing import Union
from dataclasses import dataclass
import degooged_tube.config as cfg
from degooged_tube.ytapiHacking.jsonScraping import scrapeJsonTree, ScrapeNode

import degooged_tube.ytapiHacking.controlPanel as cp



@dataclass
class YtInitalPage:
    url: str

    key: str
    clientVersion: str

    continuations: dict

    initalData: dict

    @classmethod
    def fromUrl(cls, url:str) -> Union['YtInitalPage', None]:
        r=requests.get(url)

        x, y, z = cp.apiKeyRe.search(r.text), cp.ytInitalDataRe.search(r.text), cp.clientVersionRe.search(r.text)

        if not x:
            cfg.logger.error("Unable to Find INNERTUBE_API_KEY")
            return None

        if not y:
            cfg.logger.error("Unable to Find Inital Data")
            return None

        if not z:
            cfg.logger.error("Unable to Find Youtube Client Version")
            return None

        key = x.group(1)
        initalData = json.loads(y.group(1))
        clientVersion = z.group(1)

        a = scrapeJsonTree(initalData, cp.continuationScrapeFmt)
        assert type(a) is list
        continuations = {}
        for continuation in a:
            try:
                token = continuation['token']
                apiUrl = continuation['apiUrl']
            except KeyError:
                continue

            if apiUrl in continuations:
                if token not in continuations[apiUrl]:
                    continuations[apiUrl].append(token)
                    cfg.logger.debug(f"Adding Additional Token to {apiUrl} of Page {url}\nNum Tokens Now: {len(continuations[apiUrl])}")
            else:
                continuations[apiUrl] = [token]

        return cls(url, key, clientVersion, continuations, initalData )

    def getContinuationTokens(self, apiUrl: str):
        try:
            return self.continuations[apiUrl].copy()
        except KeyError:
            raise Exception(
                f"apiUrl: {apiUrl} \n"
                f"Does Not Match Any apiUrls: {self.continuations.keys()}\n"
                f"In Inital Page: {self.url}\n"
            )



@dataclass()
class YtContIter:
    initalPage: YtInitalPage
    endOfData:bool

    apiUrl: str
    continuationTokens: list[str]

    getInitData = False
    initalData: Union[dict, None] = None

    def __init__(self, initalPage: YtInitalPage, apiUrl: str, getInitalData:bool = False):
        self.endOfData = False
        self.initalPage = initalPage

        self.continuationTokens = initalPage.getContinuationTokens(apiUrl)

        if getInitalData:
            if initalPage.initalData is None:
                raise Exception("No Inital Data To Get")

            self.initalData = initalPage.initalData
            self.getInitData = True

        self.apiUrl = apiUrl.strip('/')


    def getNext(self, dataFmt: ScrapeNode) -> Union[dict, list, None]:
        # gets element that was sent on page load
        if self.getInitData:
            self.getInitData = False
            cfg.logger.debug(f"Returning InitalData for {self.apiUrl} of {self.initalPage.url}")
            d = scrapeJsonTree(self.initalPage.initalData, dataFmt)
            return d

        if self.endOfData:
            return None

        elif len(self.continuationTokens) > 1:
            cfg.logger.debug(f"YtApiContIter for {self.apiUrl} of {self.initalPage.url} \nHas {len(self.continuationTokens)} Continuation Tokens, Iterating Through Them...")


        while True:
            if len(self.continuationTokens) == 0:
                cfg.logger.error(
                        f"YtApiContIter for {self.apiUrl} of {self.initalPage.url} \n"
                        f"Has No Continuation Tokens!\n"
                        f"This Means the Data Scraping Format Does Not Match The Data Found at The Url:\n"
                        f"{dataFmt}"
                )
                return None

            continuationToken = self.continuationTokens[0]

            requestData = cp.apiContinuationBodyFmt.format(clientVersion = self.initalPage.clientVersion, continuationToken = continuationToken)

            reqUrl = cp.apiContinuationUrlFmt.format(apiUrl = self.apiUrl, key = self.initalPage.key)

            b = requests.post(reqUrl, data=requestData)

            if b.status_code != 200:
                cfg.logger.error(
                        f"Error Sending Post Request to: {reqUrl}\n"
                        f"clientVersion: {self.initalPage.clientVersion}\n"
                        f"continuationToken: {continuationToken}\n"
                        f"Status {b.status_code} {b.reason}\n"
                        f"Request Data:\n"
                        f"{requestData}"
                )
                return None
            else:
                cfg.logger.debug(
                    f"Sent Post Request to: {reqUrl} \n"
                    f"clientVersion: {self.initalPage.clientVersion}\n"
                    f"continuationToken: {continuationToken}\n"
                    f"Status {b.status_code} {b.reason}"
                )
            
            data:dict = json.loads(b.text)
            d = scrapeJsonTree(data, dataFmt)

            if len(d) == 0:
                cfg.logger.debug(f"YtApiContIter, Removing Continuation Token for {self.apiUrl} of {self.initalPage.url} \nDoes Not Match Data Json Scraper")
                self.continuationTokens.pop(0)
                continue

            x = cp.continuationTokenRe.search(b.text)
            if not x:
                self.endOfData = True
                cfg.logger.debug(f"Reached End of Continuation Chain, Yeilding Last Result")

            else:
                self.continuationTokens = [x.group(1)]

            return d
