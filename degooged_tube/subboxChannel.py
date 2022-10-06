from dataclasses import dataclass
import degooged_tube.ytApiHacking as ytapih
import degooged_tube.config as cfg
from typing import Union


class ChannelLoadIssue(Exception):
    pass

@dataclass
class SubBoxChannel:
    channelInfo:ytapih.ChannelInfo

    uploadList: ytapih.YtApiList[ytapih.Upload]
    channelName: str
    channelId: str
    channelUrl:  str
    _extensionIndex: int
    tags: set[str]

    playlistsList: Union[ytapih.YtApiList[ytapih.ChannelPlaylist], None]

    @classmethod
    def fromInitalPage(cls, initalPage: ytapih.YtInitalPage, channelTags:set[str]) -> 'SubBoxChannel':
        channelUrl = ytapih.sanitizeChannelUrl(initalPage.url) # to keep channelUrl consistant
        try:
            channelInfo = ytapih.getChannelInfoFromInitalPage(initalPage)
            channelName = channelInfo.channelName
            channelId = channelInfo.channelId
            avatar = channelInfo.avatar
            uploadList = ytapih.getUploadList(initalPage, channelName = channelName, channelUrl= channelUrl, channelId = channelId, avatar=avatar)
        except Exception as e:
            cfg.logger.debug(e, exc_info=True)
            raise ChannelLoadIssue(channelUrl)

        return cls(channelInfo, uploadList, channelName, channelId, channelUrl, 0, channelTags, None)

    @classmethod
    def fromUrl(cls, url: str, channelTags:set[str]) -> 'SubBoxChannel':
        initalPage = ytapih.YtInitalPage.fromUrl( ytapih.sanitizeChannelUrl(url, ytapih.ctrlp.channelVideoPath) )
        return cls.fromInitalPage(initalPage, channelTags)


    def getPlaylists(self):
        if self.playlistsList is not None:
            return self.playlistsList
        initalPage = ytapih.YtInitalPage.fromUrl( ytapih.sanitizeChannelUrl(self.uploadList.getInitalPage().url, ytapih.ctrlp.channelPlaylistsPath) )
        self.playlistsList = ytapih.getChannelPlaylistsList(initalPage)
        return self.playlistsList

    
    def __repr__(self):
        tags = f'tags: {self.tags}' if len(self.tags) > 0 else 'tags: {}'
        return f'{self.channelName}\n     > {tags} - URL: {self.channelUrl}'

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        if not isinstance(other,SubBoxChannel):
            return False

        if self.channelId and other.channelId:
            if self.channelId == other.channelId:
                return True
            return False

        #backup if ids are missing
        if self.channelName == other.channelName:
            return True
        return False


    def popNextUploadInQueue(self):
        upload = self.uploadList[self._extensionIndex]
        self._extensionIndex += 1
        return upload

    def peekNextUploadInQueue(self):
        upload = self.uploadList[self._extensionIndex]
        return upload


# targets for multiprocessing maps
def loadChannel(data) -> Union[SubBoxChannel, str]:
    url, channelTags = data
    try:
        subboxChannel = SubBoxChannel.fromUrl(
            url, 
            channelTags
        )
        cfg.logger.debug(f"here: {subboxChannel.channelName}")
        return subboxChannel
    except ChannelLoadIssue:
        cfg.logger.debug("Channel Load Issue Triggered")
        # if theres an error, return the url so it can be printed in error message
        return url

def callReload(subboxChannel:SubBoxChannel):
    subboxChannel.reload()
