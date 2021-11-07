import unittest
import inspect

import degooged_tube.ytApiHacking as ytapih
import degooged_tube.config as cfg
from degooged_tube.subbox import SubBox
from .unitTests import logName


class test_SubBox(unittest.TestCase):
    subscribed = ['https://www.youtube.com/c/MattMcMuscles', 'https://www.youtube.com/channel/UC3ltptWa0xfrDweghW94Acg']
    channelUrls = [ ytapih.sanitizeChannelUrl(url) + '/videos' for url in subscribed ]
    subBox = SubBox.fromUrls(channelUrls)

    def test_noOverlap(self):
        logName(self, inspect.currentframe())
        pageSize = 10

        uploads1 = self.subBox.getPaginatedUploads(1, pageSize)

        videoIds1 = [upload['videoId'] for upload in uploads1]

        uploads2 = self.subBox.getPaginatedUploads(2, pageSize)
        videoIds2 = [upload['videoId'] for upload in uploads2]

        intersection = list( set(videoIds1)&set(videoIds2) )

        if len(intersection) != 0:
            cfg.logger.error(f"SubBox Pages Overlap:\n"
                f"Page 1:         {videoIds1}\n"
                f"Page 2:         {videoIds2}\n"
                f"Intersection 2: {intersection}\n"
            )
            self.fail()

    def test_noMisses(self):
        logName(self, inspect.currentframe())
        pageSize = 10

        page1 = self.subBox.getPaginatedUploads(1, pageSize)


        videoIds = [upload['videoId'] for upload in page1]

        self.assertEqual(pageSize, len(videoIds))
        
        count = 0
        for channel in self.subBox.channels:
            for upload in channel.uploadList:
                if upload['videoId'] in videoIds:
                    count+=1
                else:
                    break

        self.assertEqual(count, pageSize)

    def test_ordering(self):
        logName(self, inspect.currentframe())
        pageSize = 10

        page1 = self.subBox.getPaginatedUploads(1, pageSize)

        for i in range(0,len(page1)-1):
            upload1 = page1[i]
            upload2 = page1[i+1]
            self.assertNotEqual(upload1['videoId'],upload2['videoId'])

            self.assertGreaterEqual(upload1['unixTime'], upload2['unixTime'])
