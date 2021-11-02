from degooged_tube.ytapiHacking.ytContIter import YtContIter
from degooged_tube.ytapiHacking.jsonScraping import scrapeJsonTree, ScrapeNode, ScrapeNum
import degooged_tube.config as cfg
import json as json

class YtApiList:
    _list: list
    _iter: YtContIter
    _scrapeFmt: ScrapeNode
    _index: int = 0

    url: str
    contUrlFragment: str
    atMaxLen: bool = False

    def __init__(self, url, contUrlFragment, scrapeFmt, initalData:bool = False):
        self._list = []
        self.url = url
        self.contUrlFragment = contUrlFragment

        tmp = YtContIter.fromUrl(url, contUrlFragment, initalData) 

        if tmp == None:
            raise(Exception(f"Error Creating YtList for Url {url}"))

        self._iter = tmp
        self._scrapeFmt = ScrapeNode("continuationItems",ScrapeNum.All,[scrapeFmt])

        if initalData:
            initScrapeFmt = ScrapeNode("tabs",ScrapeNum.All,[scrapeFmt])
            self._extend(initScrapeFmt)

    def _extend(self,fmt):
        data = self._iter.getNext()

        if data == None:
            self.atMaxLen = True
            return

        resContainer = []
        scrapeJsonTree(data, fmt, resContainer)
        resContainer = resContainer[0]
        #print(json.dumps(resContainer, indent=4, sort_keys=True))
        #exit()

        if len(resContainer) == 0:
            cfg.logger.error(f'Scraping Json for url: "{self.url}" with Continuation Fragment: "{self.contUrlFragment}" Returned a List of Zero Length\n Scraping Format:\n{str(self._scrapeFmt)}')
            self.atMaxLen = True
            return

        res = resContainer[0]

        for r in resContainer:
            if len(r) > 0:
                res = r
                break

        if len(res) == 0:
            cfg.logger.error(f'Scraping Json for url: "{self.url}" with Continuation Fragment: "{self.contUrlFragment}" Returned a List of Zero Length\n Scraping Format:\n{str(self._scrapeFmt)}')
            self.atMaxLen = True
            return

        self._list.extend(res)

    def __len__(self):
        return len(self._list)

    def __getitem__(self, index):
        while True:
            if 0 <= index < len(self._list):
                return self._list[index]

            if 0 > index >= -len(self._list):
                return self._list[index]

            if self.atMaxLen:
                raise IndexError

            self._extend(self._scrapeFmt)

    def __next__(self):
        try:
            val = self[self.index]
            self.index += 1
            return val
        except IndexError:
            self.index = 0
            raise StopIteration
        

