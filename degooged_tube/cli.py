import degooged_tube.ytApiHacking as ytapih
import logging
import degooged_tube.config as cfg
from dataclasses import dataclass

def setupLogger():
    stream = logging.StreamHandler()
    cfg.logger.setLevel(logging.DEBUG)
    stream.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    cfg.logger.addHandler(stream)

class EndOfSubBox(Exception):
    pass

class NoVideo(Exception):
    pass


@dataclass
class SubBox:
    uploadLists: list[ytapih.YtApiList]
    extensionIndices: list[int]
    atMaxLen: bool

    orderedUploads: list
    prevOrdering: list[str]
    

    def __init__(self, uploadLists: list[ytapih.YtApiList], prevOrdering: list):
        self.extensionIndices = [0]*len(uploadLists)
        self.uploadLists = uploadLists
        self.orderedUploads = []

        self.atMaxLen = False

        if prevOrdering != []:
            raise NotImplementedError
        self.prevOrdering = prevOrdering


    @classmethod
    def fromInitalPages(cls, initalPages: list[ytapih.YtInitalPage], prevOrdering:list = list()) -> 'SubBox':
        uploadLists = [ytapih.getUploadList(initalPage) for initalPage in initalPages]
        return cls(uploadLists,prevOrdering)


    @classmethod
    def fromUrls(cls, urls, prevOrdering:list = list()) -> 'SubBox':
        uploadLists = [ ytapih.getUploadList( ytapih.YtInitalPage.fromUrl(url) ) for url in urls ]
        return cls(uploadLists, prevOrdering)


    def _getNextChannelWithMoreUploads(self, startIndex: int):
        channelIndex = startIndex

        while channelIndex < len(self.uploadLists):
            channel = self.uploadLists[channelIndex]
            nextUploadIndex = self.extensionIndices[channelIndex]
            try:
                return channelIndex, channel, channel[nextUploadIndex] 
            except IndexError:
                channelIndex+=1

        raise NoVideo

    def _appendNextUpload(self):
        if self.atMaxLen:
            cfg.logger.debug("End of SubBox Reached!")
            raise EndOfSubBox

        try:
            mostRecentIndex, _, mostRecentVideo = self._getNextChannelWithMoreUploads(0)
        except NoVideo: 
            self.atMaxLen = True
            cfg.logger.debug("End of SubBox Reached!")
            raise EndOfSubBox

        contenderIndex = mostRecentIndex 
        while True:
            try:
                contenderIndex, _, contenderVideo = self._getNextChannelWithMoreUploads(contenderIndex+1)
            except NoVideo:
                break

            if contenderVideo['unixTime'] < mostRecentVideo['unixTime']:
                mostRecentIndex = contenderIndex
                mostRecentVideo = contenderVideo

        self.orderedUploads.append(mostRecentVideo)
        self.extensionIndices[mostRecentIndex] += 1

            

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


def exampleCode1():
    channelData = ytapih.getChannelInfo('https://www.youtube.com/c/MattMcMuscles')
    uploadsUrl = 'https://www.youtube.com' + channelData['baseUrl'] + '/videos'

    uploadsPage = ytapih.YtInitalPage.fromUrl(uploadsUrl)
    uploads = ytapih.getUploadList(uploadsPage)

    upload = uploads[20]

    videoUrl = f"https://www.youtube.com/watch?v={upload['videoId']}"
    videoPage = ytapih.YtInitalPage.fromUrl(videoUrl)
    if videoPage is None:
        raise Exception("Error Getting Page for video")

    relatedVideos = ytapih.getRelatedVideoList(videoPage)
    print(relatedVideos[10])

    comments = ytapih.getCommentList(videoPage)
    print(comments[10])


def cli():
    setupLogger()
    subscribed = ['https://www.youtube.com/c/MattMcMuscles', 'https://www.youtube.com/channel/UC3ltptWa0xfrDweghW94Acg']
    channelUrlGenerator = ( ytapih.sanitizeChannelUrl(url) + '/videos' for url in subscribed )
    subBox = SubBox.fromUrls(channelUrlGenerator)

    uploads1 = subBox.getPaginatedUploads(1, 10)

    videoIds1 = [upload['videoId'] for upload in uploads1]

    uploads2 = subBox.getPaginatedUploads(2, 10)
    videoIds2 = [upload['videoId'] for upload in uploads2]

    intersection = list( set(videoIds1)&set(videoIds2) )
    if len(intersection) != 0:
        print(videoIds1)
        print(videoIds2)
        print(intersection)
        raise Exception()


    #print(json.dumps(uploads, indent = 2))

    


