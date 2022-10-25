import requests
import json
from typing import Union
from dataclasses import dataclass

from .jsonScraping import scrapeJsonTree, dumpDebugData, ScrapeError, ScrapeElement
from .ytInitalPage import YtInitalPage
from . import controlPanel as ctrlp

import degooged_tube.config as cfg

@dataclass()
class YtContIter:
    initalPage: YtInitalPage
    endOfData:bool

    apiUrl: str
    continuationTokens: list[str]
    numInitalTokens: int

    getInitData = False
    initalData: Union[dict, None] = None

    def __init__(self, initalPage: YtInitalPage, apiUrl: str, getInitalData:bool = False):
        self.apiUrl = apiUrl.strip('/')
        self.endOfData = False
        self.initalPage = initalPage

        try:
            self.continuationTokens = initalPage.getContinuationTokens(self.apiUrl)
        except Exception as e:
            if cfg.testing and not getInitalData:
                raise e

            cfg.logger.debug(e)
            self.continuationTokens = []

        self.numInitalTokens = len(self.continuationTokens)

        if getInitalData:
            if initalPage.initalData is None:
                raise Exception("No Inital Data To Get")

            self.initalData = initalPage.initalData
            self.getInitData = True

    @classmethod
    def fromUrl(cls, url, apiUrl: str, getInitalData:bool = False):
        initalPage = YtInitalPage.fromUrl(url)
        return cls(initalPage, apiUrl, getInitalData)

    def reload(self):
        self.endOfData = False
        self.initalPage = YtInitalPage.fromUrl(self.initalPage.url)

        try:
            self.continuationTokens = self.initalPage.getContinuationTokens(self.apiUrl)
        except Exception as e:
            if cfg.testing:
                raise e

            cfg.logger.debug(e)
            self.continuationTokens = []

        self.numInitalTokens = len(self.continuationTokens)

        if self.getInitData:
            if self.initalPage.initalData is None:
                raise Exception("No Inital Data To Get")

            self.initalData = self.initalPage.initalData


    def getNext(self, dataFmt: Union[ScrapeElement, list[ScrapeElement]]) -> Union[dict, list, None]:
        # gets element that was sent on page load
        if self.getInitData:
            self.getInitData = False
            cfg.logger.debug(f"Returning InitalData for {self.apiUrl} of {self.initalPage.url}")
            return self.initalPage.scrapeInitalData(dataFmt)


        if self.endOfData or self.numInitalTokens == 0:
            return None

        elif len(self.continuationTokens) > 1:
            cfg.logger.debug(f"YtApiContIter for {self.apiUrl} of {self.initalPage.url} \nHas {len(self.continuationTokens)} Continuation Tokens, Iterating Through Them...")


        # Sets up test only debug data to catch errors with scraping
        if cfg.testing:
            debugData = []
        else:
            debugData = None


        while True:

            if len(self.continuationTokens) == 0:
                cfg.logger.debug(
                    f"YtApiContIter for {self.apiUrl} of {self.initalPage.url} \n"
                    f"Has No Continuation Tokens!\n"
                    f"This Means the Data Scraping Format Does Not Match The Data Found at The Url:\n"
                    f"{dataFmt}"
                )

                dumpDebugData(debugData, cfg.testDataDumpPath)

                if cfg.testing:
                    raise ScrapeError

                self.endOfData = True
                return  None


            continuationToken = self.continuationTokens[0]

            requestData = ctrlp.apiContinuationBodyFmt.format(clientVersion = self.initalPage.clientVersion, continuationToken = continuationToken)

            reqUrl = ctrlp.apiContinuationUrlFmt.format(apiUrl = self.apiUrl, key = self.initalPage.key)

            b = requests.post(reqUrl, data=requestData)

            if b.status_code != 200:
                cfg.logger.debug(
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

            try:
                d = scrapeJsonTree(data, dataFmt, debugDataList=debugData)
            except ScrapeError:
                cfg.logger.debug(f"YtApiContIter, Removing Continuation Token for {self.apiUrl} of {self.initalPage.url} \nDoes Not Match Data Json Scraper")
                self.continuationTokens.pop(0)
                continue

            x = ctrlp.continuationTokenRe.search(b.text)
            if not x:
                self.endOfData = True
                cfg.logger.debug(f"Reached End of Continuation Chain, Yeilding Last Result")

            else:
                self.continuationTokens = [x.group(1)]

            return d


    def getNextRaw(self):
        '''Follows all continuation paths and returns their raw data, used to develop scraper formats'''

        # gets element that was sent on page load
        if self.getInitData:
            self.getInitData = False
            cfg.logger.debug(f"Returning InitalData for {self.apiUrl} of {self.initalPage.url}")
            return [self.initalPage.initalData]

        if self.endOfData:
            return None

        returnData = []
        newContinuationTokens = []
        for continuationToken in self.continuationTokens:
            requestData = ctrlp.apiContinuationBodyFmt.format(clientVersion = self.initalPage.clientVersion, continuationToken = continuationToken)
            reqUrl = ctrlp.apiContinuationUrlFmt.format(apiUrl = self.apiUrl, key = self.initalPage.key)
            b = requests.post(reqUrl, data=requestData)

            if b.status_code != 200:
                raise Exception(
                    f"Error Sending Post Request to: {reqUrl}\n"
                    f"clientVersion: {self.initalPage.clientVersion}\n"
                    f"continuationToken: {continuationToken}\n"
                    f"Status {b.status_code} {b.reason}\n"
                    f"Request Data:\n"
                    f"{requestData}"
                )
            else:
                cfg.logger.debug(
                    f"Sent Post Request to: {reqUrl} \n"
                    f"clientVersion: {self.initalPage.clientVersion}\n"
                    f"continuationToken: {continuationToken}\n"
                    f"Status {b.status_code} {b.reason}"
                )

            returnData.append(json.loads(b.text))

            x = ctrlp.continuationTokenRe.search(b.text)
            if x:
                newContinuationTokens.append(x)


        if len(newContinuationTokens) == 0:
            cfg.logger.debug(f"Reached End of Continuation Chain, Yeilding Last Result")
            self.endOfData = True

        self.continuationTokens = newContinuationTokens
        return returnData
