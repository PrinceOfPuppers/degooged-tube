import requests
import json
from dataclasses import dataclass
from typing import Union

from .jsonScraping import scrapeJsonTree, scrapeFirstJson, ScrapeElement, ScrapeError, dumpDebugData
from . import controlPanel as ctrlp 
from . import customExceptions as ce 


import degooged_tube.config as cfg

def dumpInitalRequestDebugData(requestText: str, reName: str, reText: str):
    with open(cfg.testDataDumpPath, 'w') as f:
        f.write(f"\nInital Request:\n==================================================\n")
        f.write(requestText)
        f.write('\n'+ f'Missing RE {reName}: {reText}')


@dataclass
class YtInitalPage:
    url: str

    key: str
    clientVersion: str

    continuations: Union[dict, None]

    initalData: dict

    @classmethod
    def fromUrl(cls, url:str) -> 'YtInitalPage':
        try:
            r=requests.get(url)
        except Exception as e:
            cfg.logger.debug(f"Get Request Error:\n{e}")
            raise ce.UnableToGetPage(f"Get Request Failed: {e}")

        if r.status_code != 200:
            raise requests.HTTPError(
                f"Error Sending GET Request to: {url}\n"
                f"Status: {r.status_code} {r.reason}"
            )

        x, y, z = ctrlp.apiKeyRe.search(r.text), ctrlp.ytInitalDataRe.search(r.text), ctrlp.clientVersionRe.search(r.text)


        if not x:
            if cfg.testing:
                dumpInitalRequestDebugData(r.text, "apiKeyRe", ctrlp.apiKeyRe.pattern)
            raise ce.UnableToGetPage("Unable to Find INNERTUBE_API_KEY")

        if not y:
            if cfg.testing:
                dumpInitalRequestDebugData(r.text, "ytInitalDataRe", ctrlp.ytInitalDataRe.pattern)
            raise ce.UnableToGetPage("Unable to Find Inital Data")


        if not z:
            if cfg.testing:
                dumpInitalRequestDebugData(r.text, "clientVersionRe", ctrlp.clientVersionRe.pattern)
            raise ce.UnableToGetPage("Unable to Find Youtube Client Version")

        key = x.group(1)
        initalData = json.loads(y.group(1))
        clientVersion = z.group(1)

        try:
            a = scrapeJsonTree(initalData, ctrlp.continuationScrapeFmt, truncateThreashold = 1.0)
        except ScrapeError as e:
            cfg.logger.debug(
                f"Continuations Not Found For Url: {url}\n"
                f"Explicit ScrapeError: {e}"
            )
            continuations = None
            return cls(url, key, clientVersion, continuations, initalData)

        assert type(a) is list
        continuations = {}
        for continuation in a:
            try:
                token = continuation['token']
                apiUrl = continuation['apiUrl'].strip('/')
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
        if self.continuations is None:
            raise Exception(f"The Url {self.url} Does Not Contain Continuations")

        try:
            return self.continuations[apiUrl].copy()
        except KeyError:
            raise KeyError(
                f"apiUrl: {apiUrl} \n"
                f"Does Not Match Any apiUrls: {self.continuations.keys()}\n"
                f"In Inital Page: {self.url}\n"
            )

    def scrapeInitalData(self, dataFmt: Union[ScrapeElement, list[ScrapeElement]]):
        if cfg.testing:
            debugData = []
        else:
            debugData = None

        try:
            return scrapeJsonTree(self.initalData, dataFmt, debugDataList= debugData)
        except ScrapeError:
            dumpDebugData(debugData, cfg.testDataDumpPath)
            raise

