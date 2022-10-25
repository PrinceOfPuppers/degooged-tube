from typing import Callable

from .ytContIter import YtContIter, YtInitalPage
from .jsonScraping import ScrapeElement, ScrapeLongest
from . import controlPanel as ctrlp
from degooged_tube.helpers import paginationCalculator

import degooged_tube.config as cfg

from typing import Union, TypeVar, Generic

_T = TypeVar('_T')
class YtApiList(Generic[_T]):
    _list: list[_T]
    _iter: YtContIter
    _index: int = 0

    apiUrl: str
    atMaxLen: bool = False
    scrapeFmt: ScrapeElement
    onExtend: Callable
    onExtendKwargs:dict

    _getInitData = False
    initScrapeFmt = None

    def __init__(self, initalPage: YtInitalPage, apiUrl: str, scrapeFmt: Union[ScrapeElement, list[ScrapeElement]], getInitalData: bool= False,
                        onExtend: Callable[[list[dict]], list[_T]] = lambda res: res, onExtendKwargs = dict()):
        '''
        Notes:
            - onExtendKwargs will be passed to onExtend (used for passing data like a channel url to all its videos and etc)
        '''
        self._list = []

        self.apiUrl = apiUrl

        self._iter = YtContIter(initalPage, apiUrl, getInitalData)

        scrapeList = scrapeFmt if isinstance(scrapeFmt, list) else [scrapeFmt]

        self._scrapeFmt = ScrapeLongest(ctrlp.continuationPageDataContainerKey, scrapeList , collapse = True)

        self.onExtend = onExtend
        self.onExtendKwargs = onExtendKwargs

        if getInitalData:
            if initalPage.initalData is None:
                raise Exception("No Inital Data To Get")
            self.initScrapeFmt = ScrapeLongest(ctrlp.initalPageDataContainerKey, scrapeList, collapse = True)
            self._extend(self.initScrapeFmt)
            self._getInitData = getInitalData

    def reload(self):
        self._list.clear()
        self._index = 0
        self.atMaxLen = False
        self._iter.reload()
        if self._getInitData:
            if self._iter.initalPage.initalData is None or self.initScrapeFmt is None:
                raise Exception("No Inital Data To Get")
            self._extend(self.initScrapeFmt)

    def getInitalPage(self):
        return self._iter.initalPage

    def _extend(self, fmt):
        res = self._iter.getNext(fmt)

        if res == None:
            self.atMaxLen = True
            return

        if len(res) == 0:
            cfg.logger.error(f'Scraping Json for Api Url: "{self.apiUrl}" Returned a List of Zero Length\nScraping Format:\n{str(self._scrapeFmt)}')
            self.atMaxLen = True
            return

        self._list.extend(self.onExtend(res, **self.onExtendKwargs))

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

    def __setitem__(self, index:int, val:_T):
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

    def __len__(self) -> int:
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

    def __next__(self) -> _T:
        try:
            val = self[self.index]
            self.index += 1
            return val
        except IndexError:
            self.index = 0
            raise StopIteration

    def getLimitOffset(self, limit:int, offset:int) -> list[_T]:
        res:list[_T] = []
        while offset + limit > len(self._list):
            if self.atMaxLen:
                break
            self._extend(self._scrapeFmt)

        upperBound = min(limit+offset, len(self._list))
        for i in range(offset, upperBound):
            res.append(self._list[i])

        return res

    def getPaginated(self, pageNum:int, pageSize:int) -> list[_T]:
        limit, offset = paginationCalculator(pageNum, pageSize)
        return self.getLimitOffset(limit, offset)

