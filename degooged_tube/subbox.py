import degooged_tube.ytApiHacking as ytapih
import degooged_tube.config as cfg
from dataclasses import dataclass

class EndOfSubBox(Exception):
    pass

class NoVideo(Exception):
    pass

@dataclass
class SubBoxChannel:
    uploadList: ytapih.YtApiList
    channelUrl:  str
    extensionIndex: int


class SubBox:
    channels: list[SubBoxChannel]

    atMaxLen: bool

    orderedUploads: list
    prevOrdering: list[str]
    

    def __init__(self, uploadLists: list[ytapih.YtApiList], channelUrls: list[str], prevOrdering: list):

        if len(uploadLists) != len(channelUrls):
            raise Exception("Upload Lists and Channel Urls must be Same Length")

        self.channels = []
        for i in range(len(uploadLists)):
            self.channels.append(
                SubBoxChannel(
                    uploadLists[i], channelUrls[i], 0
                )
            )

        self.orderedUploads = []

        self.atMaxLen = False

        if prevOrdering != []:
            raise NotImplementedError
        self.prevOrdering = prevOrdering


    @classmethod
    def fromInitalPages(cls, initalPages: list[ytapih.YtInitalPage], prevOrdering:list = list()) -> 'SubBox':
        uploadLists = [ytapih.getUploadList(initalPage) for initalPage in initalPages]
        channelUrls = [initalPage.url for initalPage in initalPages]
        return cls(uploadLists, channelUrls, prevOrdering)


    @classmethod
    def fromUrls(cls, urls: list[str], prevOrdering:list = list()) -> 'SubBox':
        uploadLists = [ ytapih.getUploadList( ytapih.YtInitalPage.fromUrl(url) ) for url in urls ]
        return cls(uploadLists, urls, prevOrdering)


    def _getNextChannelWithMoreUploads(self, startIndex: int):
        channelIndex = startIndex

        while channelIndex < len(self.channels):
            channel = self.channels[channelIndex]
            try:
                return channelIndex, channel, channel.uploadList[channel.extensionIndex] 
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

            if contenderVideo['unixTime'] < mostRecentVideo['unixTime']:
                mostRecentIndex = contenderIndex
                mostRecentChannel = contenderChannel
                mostRecentVideo = contenderVideo

        # All uploads must be labeled with channel url in case channel needs to be removed from subbox
        mostRecentVideo['channelUrl'] = mostRecentChannel.channelUrl
        self.orderedUploads.append(mostRecentVideo)
        mostRecentChannel.extensionIndex += 1
            

    def _extendOrderedUploads(self, desiredLen: int):
        initalLength = len(self.orderedUploads) 
        numExtend = desiredLen - initalLength
        for _ in range(numExtend):
            self._appendNextUpload()

        cfg.logger.debug(
            f"SubBox Extenion Requested:\n"
            f"Length Before Extension: {initalLength}\n"
            f"Desired Length: {desiredLen}\n"
            f"Length After Extenion: {len(self.orderedUploads)}"
        )


    def getUploads(self, limit: int, offset: int):
        desiredLen = limit + offset
        try:
            self._extendOrderedUploads(desiredLen)
        except EndOfSubBox:
            pass
        start = min(offset, len(self.orderedUploads))
        end = min(offset+limit, len(self.orderedUploads))
        if start >= end:
            cfg.logger.debug(f"SubBox.getUploads(limit= {limit}, offset= {offset}), Returning Empty List")
            return []

        return self.orderedUploads[offset: offset+limit]

    def getPaginatedUploads(self, pageNum: int, pageSize: int):
        limit = pageSize
        offset = (pageNum - 1)*pageSize
        return self.getUploads(limit, offset)

    def addChannelFromInitalPage(self, initalPage: ytapih.YtInitalPage):
        channelUploadList = ytapih.getUploadList(initalPage)
        channelUploadIndex = 0

        orderedUploadIndex = 0
        while orderedUploadIndex < len(self.orderedUploads):
            c1Upload = channelUploadList[channelUploadIndex]
            orderedUpload = self.orderedUploads[orderedUploadIndex]

            if c1Upload['unixTime'] < orderedUpload['unixTime']:
                self.orderedUploads.insert(orderedUploadIndex, c1Upload)
                channelUploadIndex+=1
                orderedUploadIndex+=1

            orderedUploadIndex+=1

        self.channels.append(
            SubBoxChannel(channelUploadList, initalPage.url, channelUploadIndex)
        )

    def addChannelFromUrl(self, url: str):
        self.addChannelFromInitalPage(ytapih.YtInitalPage.fromUrl(url))

    def removeChannel(self, channelIndex: int):
        channelUrl = self.channels[channelIndex].channelUrl

        i = 0
        while i < len(self.orderedUploads):
            upload = self.orderedUploads[i]
            if upload['channelUrl'] != channelUrl:
                i+=1
                continue

            self.orderedUploads.pop(i)

        self.channels.pop(channelIndex)
