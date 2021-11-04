import requests
import json
from typing import Union
from dataclasses import dataclass
import degooged_tube.config as cfg
from degooged_tube.ytapiHacking.jsonScraping import scrapeJson

import degooged_tube.ytapiHacking.controlPanel as cp

@dataclass
class YtInitalPage:
    url: str
    apiUrls: list[str] # empty if initalData is None

    key: str
    continuationToken: str
    clientVersion: str

    initalData: Union[dict, None] = None

    @classmethod
    def fromUrl(cls, url:str, getDataInScript:bool = False) -> Union['YtInitalPage', None]:
        r=requests.get(url)

        x, y, z = cp.apiKeyRe.search(r.text), cp.continuationTokenRe.search(r.text), cp.clientVersionRe.search(r.text)

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

        apiUrls = []

        if getDataInScript:
            w = cp.ytInitalDataRe.search(r.text)
            if not w:
                cfg.logger.error("Unable to Find ScriptData")
                return None
            initalData = json.loads(w.group(1))
            scrapeJson(initalData, 'apiUrl', apiUrls) 
            apiUrls = list(set(apiUrls))

            return cls(url, apiUrls, key, continuationToken, clientVersion, initalData)

        return cls(url, apiUrls, key, continuationToken, clientVersion)


@dataclass()
class YtContIter:
    initalPage: YtInitalPage
    endOfData:bool

    apiUrl: str
    continuationToken: str

    getInitData = False
    initalData: Union[dict, None] = None

    def __init__(self, initalPage: YtInitalPage, apiUrl: str, getInitalData:bool = False):
        self.endOfData = False
        self.initalPage = initalPage

        if getInitalData:
            if initalPage.initalData is None:
                raise Exception("No Inital Data To Get")

            self.initalData = initalPage.initalData
            self.getInitData = True

        self.continuationToken = initalPage.continuationToken

        self.apiUrl = apiUrl.strip('/')

    def getNext(self) -> Union[dict, None]:
        # gets element that was sent on page load
        if self.getInitData:
            self.getInitData = False
            return self.initalPage.initalData

        if self.endOfData:
            return None

        requestData = cp.apiContinuationBodyFmt.format(clientVersion = self.initalPage.clientVersion, continuationToken = self.continuationToken)

        reqUrl = cp.apiContinuationUrlFmt.format(apiUrl = self.apiUrl, key = self.initalPage.key)

        b = requests.post(reqUrl, data=requestData)

        if b.status_code != 200:
            cfg.logger.error(
                    f"Error Sending Post Request to: {reqUrl}\n"
                    "clientVersion: {self.initalPage.clientVersion}\n"
                    "continuationToken: {self.continuationToken}\n"
                    "Status {b.status_code} {b.reason}\n"
                    "Request Data:\n"
                    "{requestData}"
            )
            return None
        else:
            cfg.logger.debug(f"Sent Post Request to: {reqUrl} \nclientVersion: {self.initalPage.clientVersion}\ncontinuationToken: {self.continuationToken}\nStatus {b.status_code} {b.reason}")
        
        x = cp.continuationTokenRe.search(b.text)

        if not x:
            self.endOfData = True
            cfg.logger.debug(f"Reached End of Continuation Chain, Yeilding Last Result")
        else:
            self.continuationToken = x.group(1)


        data:dict = json.loads(b.text)
        return data
