from degooged_tube.ytapiHacking.ytContIter import YtContIter, YtInitalPage
from degooged_tube.ytapiHacking.jsonScraping import scrapeJsonTree, ScrapeNode, ScrapeNum
import degooged_tube.config as cfg

import degooged_tube.ytapiHacking.controlPanel as cp

from typing import Callable

class YtApiList:
    _list: list
    _iter: YtContIter
    _scrapeFmt: ScrapeNode
    _index: int = 0

    apiUrl: str
    atMaxLen: bool = False
    onExtend: Callable

    def __init__(self, initalPage: YtInitalPage, apiUrl: str, scrapeFmt: ScrapeNode, getInitalData: bool= False, onExtend: Callable = lambda res: res):
        print(apiUrl)
        self._list = []

        self.apiUrl = apiUrl

        self._iter = YtContIter(initalPage, apiUrl, getInitalData)
        self._scrapeFmt = ScrapeNode(cp.continuationPageDataContainerKey,ScrapeNum.Longest,[scrapeFmt], collapse = True)

        self.onExtend = onExtend

        if getInitalData:
            if initalPage.initalData is None:
                raise Exception("No Inital Data To Get")
            initScrapeFmt = ScrapeNode(cp.initalPageDataContainerKey,ScrapeNum.Longest,[scrapeFmt], collapse = True)
            self._extend(initScrapeFmt)

    def _extend(self, fmt):
        res = self._iter.getNext(fmt)

        if res == None:
            self.atMaxLen = True
            return

        if len(res) == 0:
            cfg.logger.error(f'Scraping Json for Api Url: "{self.apiUrl}" Returned a List of Zero Length\n Scraping Format:\n{str(self._scrapeFmt)}')
            self.atMaxLen = True
            return

        self._list.extend(self.onExtend(res))

    def getAll(self):
        while not self.atMaxLen:
            self._extend(self._scrapeFmt)

    def __getitem__(self, index):
        while True:
            if 0 <= index < len(self._list):
                return self._list[index]

            if 0 > index >= -len(self._list):
                return self._list[index]

            if self.atMaxLen:
                raise IndexError

            self._extend(self._scrapeFmt)

    def __setitem__(self, index, val):
        while True:
            if 0 <= index < len(self._list):
                self._list[index] = val
                return

            if 0 > index >= -len(self._list):
                self._list[index] = val
                return

            if self.atMaxLen:
                raise IndexError

            self._extend(self._scrapeFmt)

    def __len__(self):
        self.getAll()
        return len(self._list)

    def prettyString(self):
        self.getAll()
        return '[\n' + (', \n'.join('  '+ str(a) for a in self._list)) + '\n]'

    def __str__(self):
        self.getAll()
        return str(self._list)

    def __repr__(self):
        self.getAll()
        return f"{self.__class__.__name__}({str(self._list)})"  

    def __next__(self):
        try:
            val = self[self.index]
            self.index += 1
            return val
        except IndexError:
            self.index = 0
            raise StopIteration
        

