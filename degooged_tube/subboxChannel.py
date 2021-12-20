from dataclasses import dataclass
import degooged_tube.ytApiHacking as ytapih
import degooged_tube.config as cfg


class ChannelLoadIssue(Exception):
    pass

@dataclass
class SubBoxChannel:
    channelInfo:ytapih.ChannelInfo

    uploadList: ytapih.YtApiList[ytapih.Upload]
    channelName: str
    channelUrl:  str
    extensionIndex: int
    tags: set[str]

    @classmethod
    def fromInitalPage(cls, initalPage: ytapih.YtInitalPage, channelTags:set[str]) -> 'SubBoxChannel':
        channelUrl = ytapih.sanitizeChannelUrl(initalPage.url) # to keep channelUrl consistant
        try:
            channelInfo = ytapih.getChannelInfoFromInitalPage(initalPage)
            uploadList = ytapih.getUploadList(initalPage)
        except Exception as e:
            cfg.logger.debug(e, exc_info=True)
            raise ChannelLoadIssue(channelUrl)

        channelName = channelInfo.channelName

        return cls(channelInfo, uploadList, channelName, channelUrl, 0, channelTags)

    @classmethod
    def fromUrl(cls, url: str, channelTags:set[str]) -> 'SubBoxChannel':
        initalPage = ytapih.YtInitalPage.fromUrl( ytapih.sanitizeChannelUrl(url, ytapih.ctrlp.channelVideoPath) )
        return cls.fromInitalPage(initalPage, channelTags)

    
    def __repr__(self):
        tags = f'tags: {self.tags}' if len(self.tags) > 0 else 'tags: {}'
        return f'{self.channelName}\n     > {tags} - URL: {self.channelUrl}'

    def __str__(self):
        return self.__repr__()


def loadChannel(data):
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
