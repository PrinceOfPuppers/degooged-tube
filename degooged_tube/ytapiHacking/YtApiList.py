from degooged_tube.ytapiHacking.ytContIter import YtContIter
from degooged_tube.ytapiHacking.jsonScraping import scrapeJsonTree, ScrapeNode, ScrapeNum
import degooged_tube.config as cfg

from typing import Callable

class YtApiList:
    _list: list
    _iter: YtContIter
    _scrapeFmt: ScrapeNode
    _index: int = 0

    url: str
    contUrlFragment: str
    atMaxLen: bool = False
    onExtend: Callable

    def __init__(self, url, contUrlFragment, scrapeFmt, initalData:bool = False, onExtend: Callable = lambda res: res):
        self._list = []
        self.url = url
        self.contUrlFragment = contUrlFragment

        tmp = YtContIter.fromUrl(url, contUrlFragment, initalData) 

        if tmp == None:
            raise(Exception(f"Error Creating YtList for Url {url}"))

        self._iter = tmp
        self._scrapeFmt = ScrapeNode("continuationItems",ScrapeNum.Longest,[scrapeFmt], collapse = True)

        self.onExtend = onExtend

        if initalData:
            initScrapeFmt = ScrapeNode("tabs",ScrapeNum.Longest,[scrapeFmt], collapse = True)
            self._extend(initScrapeFmt)

    def _extend(self, fmt):
        data = self._iter.getNext()

        if data == None:
            self.atMaxLen = True
            return

        res = scrapeJsonTree(data, fmt)

        if len(res) == 0:
            cfg.logger.error(f'Scraping Json for url: "{self.url}" with Continuation Fragment: "{self.contUrlFragment}" Returned a List of Zero Length\n Scraping Format:\n{str(self._scrapeFmt)}')
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
        

