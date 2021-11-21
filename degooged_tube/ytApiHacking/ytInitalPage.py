import requests
import json
from dataclasses import dataclass

from .jsonScraping import scrapeJsonTree, ScrapeNode, ScrapeError, dumpDebugData
from . import controlPanel as ctrlp 
from . import customExceptions as ce 

import degooged_tube.config as cfg

@dataclass
class YtInitalPage:
    url: str

    key: str
    clientVersion: str

    continuations: dict

    initalData: dict

    @classmethod
    def fromUrl(cls, url:str) -> 'YtInitalPage':
        r=requests.get(url)

        if r.status_code != 200:
            raise requests.HTTPError(
                f"Error Sending GET Request to: {url}\n"
                f"Status: {r.status_code} {r.reason}"
            )

        x, y, z = ctrlp.apiKeyRe.search(r.text), ctrlp.ytInitalDataRe.search(r.text), ctrlp.clientVersionRe.search(r.text)

        if not x:
            raise ce.UnableToGetPage("Unable to Find INNERTUBE_API_KEY")

        if not y:
            raise ce.UnableToGetPage("Unable to Find Inital Data")

        if not z:
            raise ce.UnableToGetPage("Unable to Find Youtube Client Version")

        key = x.group(1)
        initalData = json.loads(y.group(1))
        clientVersion = z.group(1)

        a = scrapeJsonTree(initalData, ctrlp.continuationScrapeFmt, percentRequiredKeys = 0.0)

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
            raise KeyError(
                f"apiUrl: {apiUrl} \n"
                f"Does Not Match Any apiUrls: {self.continuations.keys()}\n"
                f"In Inital Page: {self.url}\n"
            )

    def scrapeInitalData(self, dataFmt: ScrapeNode):
        if cfg.testing:
            debugData = []
        else:
            debugData = None

        try:
            return scrapeJsonTree(self.initalData, dataFmt, debugDataList= debugData)
        except ScrapeError:
            dumpDebugData(debugData)
            raise

