from typing import Callable

from .ytContIter import YtContIter, YtInitalPage
from .jsonScraping import ScrapeNode, ScrapeNum
from . import controlPanel as ctrlp 

import degooged_tube.config as cfg

from typing import Union, TypeVar, Generic

_T = TypeVar('_T')
class YtApiList(Generic[_T]):
    _list: list[_T]
    _iter: YtContIter
    _index: int = 0

    apiUrl: str
    atMaxLen: bool = False
    scrapeFmt: ScrapeNode
    onExtend: Callable

    def __init__(self, initalPage: YtInitalPage, apiUrl: str, scrapeFmt: Union[ScrapeNode, list[ScrapeNode]], getInitalData: bool= False, onExtend: Callable[[list[dict]], list[_T]] = lambda res: res):
        self._list = []

        self.apiUrl = apiUrl

        self._iter = YtContIter(initalPage, apiUrl, getInitalData)

        scrapeList = scrapeFmt if isinstance(scrapeFmt, list) else [scrapeFmt]

        self._scrapeFmt = ScrapeNode(ctrlp.continuationPageDataContainerKey,ScrapeNum.Longest, scrapeList , collapse = True)

        self.onExtend = onExtend

        if getInitalData:
            if initalPage.initalData is None:
                raise Exception("No Inital Data To Get")
            initScrapeFmt = ScrapeNode(ctrlp.initalPageDataContainerKey, ScrapeNum.Longest, scrapeList, collapse = True)
            self._extend(initScrapeFmt)

    def _extend(self, fmt):
        res = self._iter.getNext(fmt)

        if res == None:
            self.atMaxLen = True
            return

        if len(res) == 0:
            cfg.logger.error(f'Scraping Json for Api Url: "{self.apiUrl}" Returned a List of Zero Length\nScraping Format:\n{str(self._scrapeFmt)}')
            self.atMaxLen = True
            return

        self._list.extend(self.onExtend(res))

    def getAll(self):
        while not self.atMaxLen:
            self._extend(self._scrapeFmt)

    def __getitem__(self, index) -> _T:
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
