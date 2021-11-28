import shelve
import os

from degooged_tube.subbox import SubBox, SubBoxChannel
from degooged_tube.helpers import createPath
import degooged_tube.config as cfg

class UserAlreadyExistsException(Exception):
    pass


def addSubToUserData(subs, channelUrl:str, tags:set[str]):
    subs[channelUrl] = {
        'tags': tags
    }


def removeSubFromUserData(subs, channelUrl: str):
    if channelUrl in subs:
        subs.pop(channelUrl)



########################
# Creation and Loading #
########################
def createNewUser(username:str, initalSubUrls: list[str] = list(), initalTags: list[set[str]] = None) -> SubBox:
    subbox = SubBox.fromUrls(initalSubUrls, initalTags);


    userPath = f"{cfg.userDataPath}/{username}"
    
    if os.path.exists(userPath) and len(os.listdir(userPath)) != 0:
        raise UserAlreadyExistsException()

    createPath(userPath)

    with shelve.open(f"{cfg.userDataPath}/{username}/data", 'c',writeback=True) as userData:
        subs = {}
        userData['subscriptions'] = subs

        for channel in subbox.channels:
            subs[channel.channelUrl] = {'tags': channel.tags}

    return subbox

def loadUserSubbox(username:str) -> SubBox:
    channelUrls = []
    channelTags = []
    with shelve.open(f"{cfg.userDataPath}/{username}/data", 'c',writeback=True) as userData:
        subs = userData['subscriptions']
        assert isinstance(subs,dict)
        for channelUrl in subs.keys():
            channelUrls.append(channelUrl)
            channelTags.append(subs[channelUrl]['tags'])

    return SubBox.fromUrls(channelUrls, channelTags)

def getUsers() -> list[str]:
    if not os.path.exists(cfg.userDataPath):
        return []
    return os.listdir(path=cfg.userDataPath) 




###########################
# Subbox State Management #
###########################
def subscribe(username:str, subbox: SubBox, channelUrl:str, tags:set[str]) -> SubBoxChannel:
    channel = subbox.addChannelFromUrl(channelUrl, tags)

    with shelve.open(f"{cfg.userDataPath}/{username}/data", 'c',writeback=True) as userData:
        addSubToUserData(userData['subscriptions'], channelUrl, tags)

    return channel


def unsubscribe(username:str, subbox: SubBox, channelUrl: str):
    try:
        _ = subbox.popChannel(subbox.getChannelIndex(channelUrl))
    except KeyError:
        cfg.logger.error(f"Not Subscribed to {channelUrl}")

    with shelve.open(f"{cfg.userDataPath}/{username}/data", 'c',writeback=True) as userData:
        removeSubFromUserData(userData['subscriptions'], channelUrl)


def addTags(username:str, subbox: SubBox, channelUrl: str, tags: set[str]):
    channel = subbox.channelDict[channelUrl]
    channel.tags.update(tags)

    with shelve.open(f"{cfg.userDataPath}/{username}/data", 'c',writeback=True) as userData:
        userData['subscriptions'][channelUrl]['tags'].update(tags)


def removeTags(username:str, subbox: SubBox, channelUrl: str, tags: set[str]):
    channel = subbox.channelDict[channelUrl]

    for tag in tags:
        channel.tags.discard(tag)

    with shelve.open(f"{cfg.userDataPath}/{username}/data", 'c',writeback=True) as userData:
        for tag in tags:
            userData['subscriptions'][channelUrl]['tags'].discard(tags)


