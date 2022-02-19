from unittest import TestCase
import inspect

import degooged_tube.config as cfg
from degooged_tube.subbox import SubBox, listsOverlap
from degooged_tube.ytApiHacking import sanitizeChannelUrl, getChannelInfo, getCommentList, getRelatedVideoList, getUploadList, \
                                       getVideoInfo, getSearchList, YtInitalPage, Upload
#import degooged_tube.ytApiHacking.controlPanel as ctrlp
from degooged_tube.tests.unitTests import logName
from degooged_tube import setupPool


def getLimitOffset(pageSize: int, numPages: int, subBox: SubBox, tags:set[str] = None) -> list[Upload]:
    uploads = []
    for pageNum in range(1,numPages + 1):
        page = subBox.getPaginated(pageNum, pageSize, tags)
        uploads.extend(page)

    return uploads

def checkNoOverlap(videoIds1, videoIds2):
    intersection = list( set(videoIds1)&set(videoIds2) )

    if len(intersection) != 0:
        cfg.logger.error(f"SubBox Pages Overlap:\n"
            f"Page 1:         {videoIds1}\n"
            f"Page 2:         {videoIds2}\n"
            f"Intersection 2: {intersection}\n"
        )
        return False
    return True

def checkNoMisses(uploads:list[Upload], subBox: SubBox, tags = list()):
    videoIds = [upload.videoId for upload in uploads]

    count = 0
    for channel in subBox.channels:
        for upload in channel.uploadList:
            if upload.videoId in videoIds:

                # ensure channnel has correct tags
                if len(tags) != 0 and not listsOverlap(channel.tags, tags):
                    cfg.logger.error(
                        f"Video Found in SubBox From Channel That Should Have Been Filtered\n"
                        f"VideoId Tags: {upload.videoId}\n"
                        f"Channel Tags: {channel.tags}\n"
                        f"SubBox Tags: {tags}\n"
                    )
                    return False

                count+=1
            else:
                break

    return count == len(uploads)

def checkNoDuplicates(uploads:list[Upload]):
    videoIds = [upload.videoId for upload in uploads]
    return len(set(videoIds)) == len(videoIds)

def checkOrdering(uploads: list[Upload]):
    for i in range(0,len(uploads)-1):
        upload1 = uploads[i]
        upload2 = uploads[i+1]
        if upload1.videoId == upload2.videoId:
            cfg.logger.error(f"Duplicate Video Ids Found For Uploads:\n{upload1}\nAnd\n{upload2}")
            return False


        if upload1.unixTime < upload2.unixTime:
            cfg.logger.error(f"Incorrect Upload Order for Uploads:\n{upload1}\nAnd\n{upload2}")
            return False

    return True

class test_SubBox(TestCase):
    subscribed = ['https://www.youtube.com/c/MattMcMuscles', 'https://www.youtube.com/channel/UC3ltptWa0xfrDweghW94Acg']
    tags = [{'gaming'}, {'speedrunning'}]
    subBox = SubBox.fromUrls(subscribed, tags)

    exception = None
    # Cleans up exception Message

    def test_noOverlap(self):
        logName(self, inspect.currentframe())
        pageSize = 10

        uploads1 = self.subBox.getPaginated(1, pageSize)

        videoIds1 = [upload.videoId for upload in uploads1]

        uploads2 = self.subBox.getPaginated(2, pageSize)
        videoIds2 = [upload.videoId for upload in uploads2]

        self.assertTrue(checkNoOverlap(videoIds1, videoIds2))

    def test_noMisses(self):
        logName(self, inspect.currentframe())
        pageSize = 10
        numPages = 2
        uploads = getLimitOffset(pageSize, numPages, self.subBox)
        self.assertTrue(checkNoMisses(uploads, self.subBox))

    def test_duplicates(self):
        logName(self, inspect.currentframe())
        pageSize = 10
        numPages = 2
        uploads = getLimitOffset(pageSize, numPages, self.subBox)
        self.assertTrue(checkNoDuplicates(uploads))


    def test_ordering(self):
        logName(self, inspect.currentframe())
        pageSize = 10
        numPages = 2

        uploads = getLimitOffset(pageSize, numPages, self.subBox)

        self.assertTrue(checkOrdering(uploads))

    def test_addRemoveChannel(self):
        logName(self, inspect.currentframe())
        pageSize = 40
        numPages = 2

        pageSizeExtension = 20

        numExtensionBeforeFail = 3

        newChannelUrl = 'https://www.youtube.com/c/GamersNexus'
        sanitizedChannelUrl = sanitizeChannelUrl(newChannelUrl)

        for _ in range(numExtensionBeforeFail):
            initalUploads = getLimitOffset(pageSize, numPages, self.subBox)
            initalVideoIds = [upload.videoId for upload in initalUploads]

            self.subBox.addChannelFromUrl(newChannelUrl)
            self.assertTrue(checkNoDuplicates(self.subBox.orderedUploads))

            uploads = getLimitOffset(pageSize, numPages, self.subBox)

            videoChannels = [
                upload.channelUrl 
                    if upload.channelUrl != '' 
                    else self.fail() 
                    for upload in uploads
            ]
            

            if sanitizedChannelUrl not in videoChannels:
                pageSize += pageSizeExtension
                self.subBox.popChannel(self.subBox.getChannelIndex(newChannelUrl))
                cfg.logger.info("videoId belonging to newly added channel not found in subbox")
                continue

            self.assertTrue(checkNoDuplicates(uploads))
            self.assertTrue(checkNoMisses(uploads, self.subBox))
            self.assertTrue(checkOrdering(uploads))

            self.subBox.popChannel(self.subBox.getChannelIndex(newChannelUrl))

            endUploads = getLimitOffset(pageSize, numPages, self.subBox)
            endVideoIds = [upload.videoId for upload in endUploads]

            self.assertTrue(checkNoDuplicates(uploads))
            self.assertTrue(checkNoMisses(endUploads, self.subBox))
            self.assertTrue(checkOrdering(endUploads))

            self.assertListEqual(initalVideoIds, endVideoIds)
            return

        self.fail()

    def test_noOverlap_tags(self):
        logName(self, inspect.currentframe())
        pageSize = 10

        uploads1 = self.subBox.getPaginated(1, pageSize, {'gaming'})

        videoIds1 = [upload.videoId for upload in uploads1]

        uploads2 = self.subBox.getPaginated(2, pageSize, {'gaming'})
        videoIds2 = [upload.videoId for upload in uploads2]

        self.assertTrue(checkNoOverlap(videoIds1, videoIds2))

    def test_noMisses_tags(self):
        logName(self, inspect.currentframe())
        pageSize = 10
        numPages = 2
        uploads = getLimitOffset(pageSize, numPages, self.subBox, {'speedrunning'})
        self.assertTrue(checkNoMisses(uploads, self.subBox, {'speedrunning'}))


    def test_ordering_tags(self):
        logName(self, inspect.currentframe())
        pageSize = 10
        numPages = 2

        uploads = getLimitOffset(pageSize, numPages, self.subBox, {'gaming'})

        self.assertTrue(checkOrdering(uploads))

    def test_filter_tags(self):
        logName(self, inspect.currentframe())
        pageSize = 10
        numPages = 2

        t = self.tags[0]
        channelUrl = self.subscribed[0]

        uploads = getLimitOffset(pageSize, numPages, self.subBox, t)

        for upload in uploads:
            self.assertEqual(upload.channelUrl, channelUrl)

    def test_reload(self):
        logName(self, inspect.currentframe())

        pageSize = 10
        self.subBox.reload()

        uploads1 = self.subBox.getPaginated(1, pageSize)
        videoIds1 = [upload.videoId for upload in uploads1]

        self.assertTrue(checkNoMisses(uploads1, self.subBox))
        self.assertTrue(checkOrdering(uploads1))
        self.assertTrue(checkNoDuplicates(uploads1))

        uploads2 = self.subBox.getPaginated(2, pageSize)
        videoIds2 = [upload.videoId for upload in uploads2]

        self.assertTrue(checkNoOverlap(videoIds1, videoIds2))





# we are checking the formats for the next section of tests, hence we dont want the onExtend callbacks to interfere
# we define this callback to override them
def nothingCallback(res):
    return res

class test_getFunctionsAndFmts(TestCase):
    channelUrl = sanitizeChannelUrl('https://www.youtube.com/c/GamersNexus')
    channelVideosUrl = sanitizeChannelUrl('https://www.youtube.com/c/GamersNexus', '/videos')
    videoUrl = 'https://www.youtube.com/watch?v=B14h25fKMpY'

    def test_getChannelInfo(self):
        logName(self, inspect.currentframe())

        _ = getChannelInfo(self.channelUrl)

    def test_getCommentList(self):
        logName(self, inspect.currentframe())
        page = YtInitalPage.fromUrl(self.videoUrl)

        commentList = getCommentList(page, onExtend = nothingCallback)
        _ = commentList[0]
        for i in range(0,20):
            _ = commentList[i]

    def test_getRelatedVideoList(self):
        logName(self, inspect.currentframe())
        page = YtInitalPage.fromUrl(self.videoUrl)

        videoList = getRelatedVideoList(page)
        _ = videoList[0]
        for i in range(0,20):
            _ = videoList[i]


    def test_getUploadList(self):
        logName(self, inspect.currentframe())
        page = YtInitalPage.fromUrl(self.channelVideosUrl)

        uploadList = getUploadList(page, onExtend = nothingCallback)
        _ = uploadList[0]
        for i in range(0,40):
            _ = uploadList[i]

    def test_getVideoInfo(self):
        logName(self, inspect.currentframe())
        page = YtInitalPage.fromUrl(self.videoUrl)

        _ = getVideoInfo(page)


    def test_getSearchList(self):
        logName(self, inspect.currentframe())
        searchVideoList, _ = getSearchList("asdf")
        for i in range(0,20):
            _ = searchVideoList[i]

class test_SpecialCases(TestCase):
    subscribed = ['https://www.youtube.com/user/Northernlion', 'https://www.youtube.com/c/SummoningSalt']
    tags = [{}, {'speedrunning'}]
    subBox = SubBox.fromUrls(subscribed, tags)

    def test_bigFilter(self):
        _ = self.subBox.getPaginated(1, 40, self.tags[1])

    def test_loadalot(self):
        _ = self.subBox.getPaginated(1, 1000)

    def test_searchFilters(self):
        logName(self, inspect.currentframe())

        numFilterTests = 10
        for i in range(0,numFilterTests):
            searchVideoList, filters = getSearchList("test")
            for i in range(0,20):
                _ = searchVideoList[i]
            filterCatigory = filters[i%len(filters)]
            filter = filterCatigory.filters[(i+3)%len(filterCatigory.filters)]
            cfg.logger.debug(f"Toggling Filter {filterCatigory.searchType} - {filter.label}")
            searchVideoList, filters = getSearchList(filter.searchUrlFragment)


if __name__ == "__main__":
    cfg.testing = True
    t = test_SpecialCases()
    t.test_searchFilters()
