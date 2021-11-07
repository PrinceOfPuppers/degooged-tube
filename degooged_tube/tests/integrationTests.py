import unittest
import inspect

import degooged_tube.config as cfg
from degooged_tube.subbox import SubBox
from degooged_tube.ytApiHacking import sanitizeChannelUrl
import degooged_tube.ytApiHacking.controlPanel as ctrlp
from .unitTests import logName


def getUploads(pageSize: int, numPages: int, subBox: SubBox):
    uploads = []
    for pageNum in range(numPages):
        page = subBox.getPaginatedUploads(pageNum, pageSize)
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

def checkNoMisses(uploads, subBox: SubBox):

    videoIds = [upload['videoId'] for upload in uploads]

    
    count = 0
    for channel in subBox.channels:
        for upload in channel.uploadList:
            if upload['videoId'] in videoIds:
                count+=1
            else:
                break

    return count == len(uploads)

def checkOrdering(uploads):
    for i in range(0,len(uploads)-1):
        upload1 = uploads[i]
        upload2 = uploads[i+1]
        if upload1['videoId'] == upload2['videoId']:
            cfg.logger.error(f"Duplicate Video Ids Found For Uploads:\n{upload1}\nAnd\n{upload2}")
            return False


        if upload1['unixTime'] < upload2['unixTime']:
            cfg.logger.error(f"Incorrect Upload Order for Uploads:\n{upload1}\nAnd\n{upload2}")
            return False

    return True

class test_SubBox(unittest.TestCase):
    subscribed = ['https://www.youtube.com/c/MattMcMuscles', 'https://www.youtube.com/channel/UC3ltptWa0xfrDweghW94Acg']
    subBox = SubBox.fromUrls(subscribed)

    def test_noOverlap(self):
        logName(self, inspect.currentframe())
        pageSize = 10

        uploads1 = self.subBox.getPaginatedUploads(1, pageSize)

        videoIds1 = [upload['videoId'] for upload in uploads1]

        uploads2 = self.subBox.getPaginatedUploads(2, pageSize)
        videoIds2 = [upload['videoId'] for upload in uploads2]

        self.assertTrue(checkNoOverlap(videoIds1, videoIds2))

    def test_noMisses(self):
        logName(self, inspect.currentframe())
        pageSize = 10
        numPages = 2
        uploads = getUploads(pageSize, numPages, self.subBox)
        self.assertTrue(checkNoMisses(uploads, self.subBox))


    def test_ordering(self):
        logName(self, inspect.currentframe())
        pageSize = 10
        numPages = 2

        uploads = getUploads(pageSize, numPages, self.subBox)

        self.assertTrue(checkOrdering(uploads))

    def test_addRemoveChannel(self):
        logName(self, inspect.currentframe())
        pageSize = 40
        numPages = 2

        pageSizeExtension = 20

        numExtensionBeforeFail = 3

        newChannelUrl = 'https://www.youtube.com/c/GamersNexus'
        sanitizedChannelUrl = sanitizeChannelUrl(newChannelUrl, ctrlp.channelVideoPath)

        for _ in range(numExtensionBeforeFail):
            initalUploads = getUploads(pageSize, numPages, self.subBox)
            initalVideoIds = [upload['videoId'] for upload in initalUploads]

            self.subBox.addChannelFromUrl(newChannelUrl)

            uploads = getUploads(pageSize, numPages, self.subBox)

            videoChannels = [upload['channelUrl'] for upload in uploads]
            

            if sanitizedChannelUrl not in videoChannels:
                pageSize += pageSizeExtension
                self.subBox.removeChannel(self.subBox.getChannelIndex(newChannelUrl))
                cfg.logger.info("videoId belonging to newly added channel not found in subbox")
                continue

            self.assertTrue(checkNoMisses(uploads, self.subBox))
            self.assertTrue(checkOrdering(uploads))

            self.subBox.removeChannel(self.subBox.getChannelIndex(newChannelUrl))

            endUploads = getUploads(pageSize, numPages, self.subBox)
            endVideoIds = [upload['videoId'] for upload in endUploads]

            self.assertTrue(checkNoMisses(endUploads, self.subBox))
            self.assertTrue(checkOrdering(endUploads))

            self.assertListEqual(initalVideoIds, endVideoIds)
            return

        self.fail()
            
