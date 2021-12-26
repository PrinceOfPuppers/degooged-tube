import degooged_tube.ytApiHacking as ytapih
import degooged_tube.config as cfg
from typing import Union, Tuple
from degooged_tube.subboxChannel import SubBoxChannel, ChannelLoadIssue, loadChannel
from degooged_tube import pool
from degooged_tube.helpers import paginationCalculator


class EndOfSubBox(Exception):
    pass

class NoVideo(Exception):
    pass

class AlreadySubscribed(Exception):
    pass



def listsOverlap(l1, l2):
    return not set(l1).isdisjoint(l2)

def setsOverlap(s1:set, s2:set):
    return not s1.isdisjoint(s2)


class SubBox:
    channels: list[SubBoxChannel]
    channelDict: dict[str, SubBoxChannel]

    atMaxLen: bool

    orderedUploads: list[ytapih.Upload]
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
    def fromUrls(cls, urls: list[str], channelTags:list[set[str]] = None, prevOrdering:list = list()) -> 'SubBox':
        cfg.logger.info("Loading SubBox... ")
        cfg.logger.debug(f"Creating SubBox From Urls:\n{urls}")

        channels = []

        if channelTags is None:
            channelTags = [set() for _ in range(len(urls))]
        else:
            assert len(urls) == len(channelTags)

        if cfg.testing or pool is None:
            channels = [loadChannel(data) for data in zip(urls, channelTags)]
        else:
            channels = pool.map(loadChannel, zip(urls, channelTags))

        for i,channel in enumerate(reversed(channels)):
            if isinstance(channel, str):
                cfg.logger.info(f"Unable to Subscribe to {channel} \nAre You Sure the URL is Correct?")
                channels.pop(i)

        # Remove Duplicate Channels
        duplicateIndices = []
        for i in range(len(channels)):
            for j in range(i+1, len(channels)):
                ch1 = channels[i]
                ch2 = channels[j]
                assert not isinstance(ch1,str)
                assert not isinstance(ch2,str)
                if ch1.channelName == ch2.channelName:
                    cfg.logger.info(f'{ch1.channelUrl} \nand \n{ch2.channelUrl} \nHave the Same Name: {ch1.channelName}, Removing Duplicate channel')
                    duplicateIndices.append(i)

        for i in duplicateIndices:
            channels.pop(i)


        return cls(channels, prevOrdering)


    def _getNextChannelWithMoreUploads(self, startIndex: int) -> Tuple[int, SubBoxChannel, ytapih.Upload]:
        channelIndex = startIndex

        while channelIndex < len(self.channels):
            channel = self.channels[channelIndex]
            try:
                return channelIndex, channel, channel.peekNextUploadInQueue()
            except IndexError:
                channelIndex+=1

        raise NoVideo

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

            if contenderVideo.unixTime > mostRecentVideo.unixTime:
                mostRecentIndex = contenderIndex
                mostRecentChannel = contenderChannel
                mostRecentVideo = contenderVideo

        self.orderedUploads.append(mostRecentChannel.popNextUploadInQueue())
            
    def _getChannelUrlsUnderTags(self, tags: set[str]):
        return [channel.channelUrl for channel in self.channels if tags.issubset(channel.tags)]

    def _numUploads(self, channelUrlWhitelist: list[str]):
        if len(channelUrlWhitelist) == 0:
            return len(self.orderedUploads)
        num = 0
        for upload in self.orderedUploads:
            if upload.channelUrl in channelUrlWhitelist:
                num+=1

        return num

    def _extendOrderedUploads(self, desiredLen: int, channelUrlWhitelist: Union[list[str], None]):
        initalLength = len(self.orderedUploads) 

        debugMessage = \
            f"SubBox Extenion Requested:\n" \
            f"Length Before Extension: {initalLength}\n" \
            f"Desired Length: {desiredLen}\n" \
            f"Length After Extenion: {len(self.orderedUploads)}"

        if channelUrlWhitelist is None or len(channelUrlWhitelist) == 0:
            numExtend = desiredLen - initalLength
            for _ in range(numExtend):
                self._appendNextUpload()

        else:
            currentLen = self._numUploads(channelUrlWhitelist)
            initalLen = currentLen
            numExtend = desiredLen - currentLen

            while numExtend > 0:
                for _ in range(numExtend):
                    self._appendNextUpload()
                currentLen = self._numUploads(channelUrlWhitelist)
                numExtend = desiredLen - currentLen

            debugMessage += f"\nSpecified Channels: {channelUrlWhitelist}"\
                            f"\nLength of Tagged Uploads Before Extension: {initalLen}"\
                            f"\nLength of Tagged Uploads After Extension: {currentLen}"\

        cfg.logger.debug(debugMessage)


    def getUploads(self, limit: int, offset: int, tags: Union[set[str], None]) -> list[ytapih.Upload]:
        desiredLen = limit + offset
        if tags is None or len(tags) == 0:
            channelUrlWhitelist = None
        else:
            channelUrlWhitelist = self._getChannelUrlsUnderTags(tags)
            if len(channelUrlWhitelist) == 0:
                cfg.logger.debug(f"Provided Tags: {tags} Exclude All Channels")
                return []

        try:
            self._extendOrderedUploads(desiredLen, channelUrlWhitelist)
        except EndOfSubBox:
            pass

        if channelUrlWhitelist is None:
            uploads = self.orderedUploads
        else:
            uploads = list(
                filter(
                    lambda upload: upload.channelUrl in channelUrlWhitelist,
                    self.orderedUploads
                )
            )


            cfg.logger.info(
                f"Filtering Subbox by Tags:{tags}\n"
                f"SubBox Len Before Filtering: {len(self.orderedUploads)}\n"
                f"SubBox Len After Filtering: {len(uploads)}\n"
                f"Desired Length: {limit + offset - 1}"
            )

        start = min(offset, len(uploads))
        end = min(offset+limit, len(uploads))
        if start >= end:
            cfg.logger.debug(f"SubBox.getUploads(limit= {limit}, offset= {offset}), Returning Empty List")
            return []
        
        return uploads[offset: offset+limit]

    def getPaginatedUploads(self, pageNum: int, pageSize: int, tags: Union[set[str], None] = None) -> list[ytapih.Upload]:
        limit, offset = paginationCalculator(pageNum, pageSize)
        return self.getUploads(limit, offset, tags)

    def addChannelFromInitalPage(self, initalPage: ytapih.YtInitalPage, tags: set[str] = set()):
        channel = SubBoxChannel.fromInitalPage(initalPage, tags)
        cfg.logger.debug(f"Adding new Channel to SubBox {channel.channelUrl}")

        for c in self.channels:
            if channel.channelName == c.channelName:
                cfg.logger.debug(f"Channel Name: {channel.channelName} Already exists in SubBox:\n{[channel.channelName for channel in self.channels]}")
                cfg.logger.error(f"You're Already Subscribed to {channel.channelName}")
                raise AlreadySubscribed()

        channelUploadIndex = 0

        orderedUploadIndex = 0
        while orderedUploadIndex < len(self.orderedUploads):
            c1Upload = channel.uploadList[channelUploadIndex]
            orderedUpload = self.orderedUploads[orderedUploadIndex]

            if c1Upload.unixTime >= orderedUpload.unixTime:
                cfg.logger.debug(
                    f"Inserting New Channel Video Into SubBox\n"
                    f"New Insert Id : {c1Upload.videoId} Unix Time: {c1Upload.unixTime} Title: {c1Upload.title}\n"
                    f"Pushed Back Id: {orderedUpload.videoId} Unix Time: {orderedUpload.unixTime} Title: {orderedUpload.title}"
                )
                self.orderedUploads.insert(orderedUploadIndex, c1Upload)
                channelUploadIndex+=1

            orderedUploadIndex+=1

        self.channels.append(
            channel
        )
        self.channelDict[channel.channelUrl] = channel

        return channel

    def addChannelFromUrl(self, url: str, tags: set[str] = set()):
        url = ytapih.sanitizeChannelUrl(url, ytapih.ctrlp.channelVideoPath)

        if url in self.channelDict.keys():
            cfg.logger.debug(f"url: {url} Already exists in SubBox Urls:\n{[channel.channelUrl for channel in self.channels]}")
            cfg.logger.info(f"You're Already Subscribed to {url}")
            raise AlreadySubscribed()

        channel = self.addChannelFromInitalPage(ytapih.YtInitalPage.fromUrl(url), tags)
        return channel


    def popChannel(self, channelIndex: int):
        channelUrl = self.channels[channelIndex].channelUrl
        cfg.logger.debug(f"Remvoing Channel from SubBox, URL: {channelUrl}")

        i = 0
        while i < len(self.orderedUploads):
            upload = self.orderedUploads[i]
            if upload.channelUrl != channelUrl:
                i+=1
                continue

            self.orderedUploads.pop(i)

        channel = self.channels[channelIndex]
        self.channelDict.pop(self.channels[channelIndex].channelUrl)
        self.channels.pop(channelIndex)

        return channel

    def getChannelIndex(self, channelUrl: str):
        channelUrl = ytapih.sanitizeChannelUrl(channelUrl)
        for channelIndex in range(len(self.channels)):
            channel = self.channels[channelIndex]
            if channel.channelUrl == channelUrl:
                return channelIndex
        cfg.logger.debug(f"Channel Urls: {[key for key in self.channelDict.keys()]}")
        raise KeyError(f"No Channel with Channel URL: {channelUrl}")

    def getAllTags(self):
        tags = set()
        for channel in self.channels:
            tags.update(channel.tags)
        return tags


