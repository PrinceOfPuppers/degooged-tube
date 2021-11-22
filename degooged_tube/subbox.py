import degooged_tube.ytApiHacking as ytapih
import degooged_tube.config as cfg
from dataclasses import dataclass
from typing import Union

class EndOfSubBox(Exception):
    pass

class NoVideo(Exception):
    pass

class AlreadySubscribed(Exception):
    pass


def listsOverlap(l1, l2):
    return not set(l1).isdisjoint(l2)

@dataclass
class SubBoxChannel:
    scrapedData:dict

    uploadList: ytapih.YtApiList
    channelUrl:  str
    extensionIndex: int
    tags: list[str]

    @classmethod
    def fromInitalPage(cls, initalPage: ytapih.YtInitalPage, channelTags:list[str]) -> 'SubBoxChannel':
        d = ytapih.getChannelInfoFromInitalPage(initalPage)
        scrapedData = d

        uploadList = ytapih.getUploadList(initalPage)
        channelUrl = d['channelUrl']

        return cls(scrapedData, uploadList, channelUrl, 0, channelTags)

    @classmethod
    def fromUrl(cls, url: str, channelTags:list[str]) -> 'SubBoxChannel':
        initalPage = ytapih.YtInitalPage.fromUrl( ytapih.sanitizeChannelUrl(url, ytapih.ctrlp.channelVideoPath) )
        return cls.fromInitalPage(initalPage, channelTags)


class SubBox:
    channels: list[SubBoxChannel]
    channelDict: dict[str, SubBoxChannel]

    atMaxLen: bool

    orderedUploads: list
    prevOrdering: list[str]
    

    def __init__(self, subBoxChannels: list[SubBoxChannel], prevOrdering: list):
        self.channels = subBoxChannels

        self.channelDict = {}

        for channel in self.channels:
            self.channelDict[channel.channelUrl] = channel

        self.orderedUploads = []

        self.atMaxLen = False

        if prevOrdering != []:
            raise NotImplementedError

        self.prevOrdering = prevOrdering


    @classmethod
    def fromInitalPages(cls, initalPages: list[ytapih.YtInitalPage], channelTags:list[list[str]] = None, prevOrdering:list = list()) -> 'SubBox':
        cfg.logger.debug(f"Creating SubBox From InitalPages")

        if channelTags is not None:
            assert len(initalPages) == len(channelTags)

        channels = []
        for i, initalPage in enumerate(initalPages):
            channels.append(
                SubBoxChannel.fromInitalPage(
                    initalPage, 
                    list() if channelTags is None else channelTags[i]
                )
            )

        return cls(channels, prevOrdering)


    @classmethod
    def fromUrls(cls, urls: list[str], channelTags = None, prevOrdering:list = list()) -> 'SubBox':
        cfg.logger.debug(f"Creating SubBox From Urls:\n{urls}")
        if channelTags is not None:
            assert len(urls) == len(channelTags)

        channels = []
        for i, url in enumerate(urls):
            channels.append(
                SubBoxChannel.fromUrl(
                    url, 
                    list() if channelTags is None else channelTags[i]
                )
            )

        return cls(channels, prevOrdering)


    def _getNextChannelWithMoreUploads(self, startIndex: int):
        channelIndex = startIndex

        while channelIndex < len(self.channels):
            channel = self.channels[channelIndex]
            try:
                return channelIndex, channel, channel.uploadList[channel.extensionIndex] 
            except IndexError:
                channelIndex+=1

        raise NoVideo

    def _insertUpload(self, index, upload, channelUrl):
        upload['channelUrl'] = channelUrl
        self.orderedUploads.insert(index,upload)

    def _appendUpload(self, upload, channelUrl):
        upload['channelUrl'] = channelUrl
        self.orderedUploads.append(upload)

    def _appendNextUpload(self):
        if self.atMaxLen:
            cfg.logger.debug("End of SubBox Reached!")
            raise EndOfSubBox

        # mostRecentIndex / contenderIndex are indices of channels, we are checking for the channel who uploaded most recently
        try:
            mostRecentIndex, mostRecentChannel, mostRecentVideo = self._getNextChannelWithMoreUploads(0)
        except NoVideo: 
            self.atMaxLen = True
            cfg.logger.debug("End of SubBox Reached!")
            raise EndOfSubBox

        contenderIndex = mostRecentIndex 
        while True:
            try:
                contenderIndex, contenderChannel, contenderVideo = self._getNextChannelWithMoreUploads(contenderIndex+1)
            except NoVideo:
                break

            if contenderVideo['unixTime'] < mostRecentVideo['unixTime']:
                mostRecentIndex = contenderIndex
                mostRecentChannel = contenderChannel
                mostRecentVideo = contenderVideo

        self._appendUpload(mostRecentVideo, mostRecentChannel.channelUrl)
        mostRecentChannel.extensionIndex += 1
            

    def _numUploadsWithTags(self, tags: list[str]):
        num = 0
        for upload in self.orderedUploads:
            channelTags = self.channelDict[upload['channelUrl']].tags
            if listsOverlap(channelTags, tags):
                num+=1

        return num

    def _extendOrderedUploads(self, desiredLen: int, tags: Union[list[str], None]):
        initalLength = len(self.orderedUploads) 

        debugMessage = \
            f"SubBox Extenion Requested:\n" \
            f"Length Before Extension: {initalLength}\n" \
            f"Desired Length: {desiredLen}\n" \
            f"Length After Extenion: {len(self.orderedUploads)}"

        if tags is None or len(tags) == 0:
            numExtend = desiredLen - initalLength
            for _ in range(numExtend):
                self._appendNextUpload()

        else:
            currentLen = self._numUploadsWithTags(tags)
            initalLen = currentLen
            numExtend = desiredLen - currentLen

            while numExtend > 0:
                for _ in range(numExtend):
                    self._appendNextUpload()
                currentLen = self._numUploadsWithTags(tags)
                numExtend = desiredLen - currentLen

            debugMessage += f"\nSpecified Tags: {tags}"
            debugMessage += f"\nLength of Tagged Uploads Before Extension: {initalLen}"
            debugMessage += f"\nLength of Tagged Uploads After Extension: {currentLen}"

        cfg.logger.debug(debugMessage)


    def getUploads(self, limit: int, offset: int, tags: Union[list[str], None]):
        desiredLen = limit + offset
        try:
            self._extendOrderedUploads(desiredLen, tags)
        except EndOfSubBox:
            pass

        if tags is None or len(tags) == 0:
            uploads = self.orderedUploads

        else:
            uploads = list(filter(lambda upload: listsOverlap(self.channelDict[upload['channelUrl']].tags, tags) , self.orderedUploads))
            cfg.logger.debug(
                f"Filtering Subbox by Tags:{tags}\n"
                f"SubBox Len Before Filtering: {len(self.orderedUploads)}"
                f"SubBox Len After Filtering: {len(uploads)}"
                f"Desired Length: {limit + offset - 1}"
            )

        start = min(offset, len(uploads))
        end = min(offset+limit, len(uploads))
        if start >= end:
            cfg.logger.debug(f"SubBox.getUploads(limit= {limit}, offset= {offset}), Returning Empty List")
            return []
        
        return uploads[offset: offset+limit]

    def getPaginatedUploads(self, pageNum: int, pageSize: int, tags: Union[list[str], None] = None):
        limit = pageSize
        offset = (pageNum - 1)*pageSize
        return self.getUploads(limit, offset, tags)

    def addChannelFromInitalPage(self, initalPage: ytapih.YtInitalPage, tags: list[str] = list()):
        channel = SubBoxChannel.fromInitalPage(initalPage, tags)
        cfg.logger.debug(f"Adding new Channel to SubBox {channel.channelUrl}")

        if channel.channelUrl in self.channelDict.keys():
            raise AlreadySubscribed()

        channelUploadIndex = 0

        orderedUploadIndex = 0
        while orderedUploadIndex < len(self.orderedUploads):
            c1Upload = channel.uploadList[channelUploadIndex]
            orderedUpload = self.orderedUploads[orderedUploadIndex]

            if c1Upload['unixTime'] >= orderedUpload['unixTime']:
                cfg.logger.debug(
                    f"Inserting New Channel Video Into SubBox\n"
                    f"New Insert Id : {c1Upload['videoId']} Unix Time: {c1Upload['unixTime']} Title: {c1Upload['title']}\n"
                    f"Pushed Back Id: {orderedUpload['videoId']} Unix Time: {orderedUpload['unixTime']} Title: {orderedUpload['title']}"
                )
                self._insertUpload(orderedUploadIndex, c1Upload, channel.channelUrl)
                channelUploadIndex+=1

            orderedUploadIndex+=1

        self.channels.append(
            channel
        )
        self.channelDict[channel.channelUrl] = channel

    def addChannelFromUrl(self, url: str, tags: list[str] = list()):
        url = ytapih.sanitizeChannelUrl(url, ytapih.ctrlp.channelVideoPath)

        if url in self.channelDict.keys():
            cfg.logger.error(f"url: {url} Already exists in SubBox Urls:\n{[channel.channelUrl for channel in self.channels]}")
            raise AlreadySubscribed()

        self.addChannelFromInitalPage(ytapih.YtInitalPage.fromUrl(url), tags)


    def removeChannel(self, channelIndex: int):
        channelUrl = self.channels[channelIndex].channelUrl
        cfg.logger.debug(f"Remvoing Channel from SubBox, URL: {channelUrl}")

        i = 0
        while i < len(self.orderedUploads):
            upload = self.orderedUploads[i]
            if upload['channelUrl'] != channelUrl:
                i+=1
                continue

            self.orderedUploads.pop(i)

        self.channelDict.pop(self.channels[channelIndex].channelUrl)
        self.channels.pop(channelIndex)

    def getChannelIndex(self, channelUrl: str):
        channelUrl = ytapih.sanitizeChannelUrl(channelUrl)
        for channelIndex in range(len(self.channels)):
            channel = self.channels[channelIndex]
            if channel.channelUrl == channelUrl:
                return channelIndex
        cfg.logger.debug(f"Channel Urls: {[key for key in self.channelDict.keys()]}")
        raise KeyError(f"No Channel with Channel URL: {channelUrl}")


