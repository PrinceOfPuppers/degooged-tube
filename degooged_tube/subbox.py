import degooged_tube.ytApiHacking as ytapih
import degooged_tube.config as cfg
from dataclasses import dataclass

class EndOfSubBox(Exception):
    pass

class NoVideo(Exception):
    pass

class AlreadySubscribed(Exception):
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
        cfg.logger.debug(f"Creating SubBox With the following Channels:\n{channelUrls}")

        return cls(uploadLists, channelUrls, prevOrdering)


    @classmethod
    def fromUrls(cls, urls: list[str], prevOrdering:list = list()) -> 'SubBox':
        uploadLists = [ ytapih.getUploadList( ytapih.YtInitalPage.fromUrl( ytapih.sanitizeChannelUrl(url, ytapih.ctrlp.channelVideoPath) ) ) for url in urls ]
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
        cfg.logger.debug(f"Adding new Channel to SubBox {initalPage.url}")
        channelUploadList = ytapih.getUploadList(initalPage)

        # heuristic to see if already subscribed (we dont have a channel id)
        # note we check multiple recent videos because channel may have uploaded new videos since last refresh
        for i in range(0,2):
            try:
                newChannelVideo = channelUploadList[i]
            except IndexError:
                pass
            else:
                for channel in self.channels:
                    try:
                        oldChannelVideo = channel.uploadList[0]
                    except IndexError:
                        continue
                    else:
                        if newChannelVideo == oldChannelVideo:
                            raise AlreadySubscribed()

        channelUploadIndex = 0

        orderedUploadIndex = 0
        while orderedUploadIndex < len(self.orderedUploads):
            c1Upload = channelUploadList[channelUploadIndex]
            orderedUpload = self.orderedUploads[orderedUploadIndex]

            if c1Upload['unixTime'] >= orderedUpload['unixTime']:
                cfg.logger.debug(
                    f"Inserting New Channel Video Into SubBox\n"
                    f"New Insert Id : {c1Upload['videoId']} Unix Time: {c1Upload['unixTime']} Title: {c1Upload['title']}\n"
                    f"Pushed Back Id: {orderedUpload['videoId']} Unix Time: {orderedUpload['unixTime']} Title: {orderedUpload['title']}"
                )
                self._insertUpload(orderedUploadIndex, c1Upload,initalPage.url)
                channelUploadIndex+=1

            orderedUploadIndex+=1

        self.channels.append(
            SubBoxChannel(channelUploadList, initalPage.url, channelUploadIndex)
        )

    def addChannelFromUrl(self, url: str):
        url = ytapih.sanitizeChannelUrl(url, ytapih.ctrlp.channelVideoPath)
        for channel in self.channels:
            if url == channel.channelUrl:
                cfg.logger.error(f"url: {url} Already exists in SubBox Urls:\n{[channel.channelUrl for channel in self.channels]}")
                raise AlreadySubscribed()
        self.addChannelFromInitalPage(ytapih.YtInitalPage.fromUrl(url))

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

        self.channels.pop(channelIndex)

    def getChannelIndex(self, channelUrl: str):
        channelUrl = ytapih.sanitizeChannelUrl(channelUrl, ytapih.ctrlp.channelVideoPath)
        for channelIndex in range(len(self.channels)):
            channel = self.channels[channelIndex]
            if channel.channelUrl == channelUrl:
                return channelIndex
        raise KeyError(f"No Channel with Channel URL: {channelUrl}")


