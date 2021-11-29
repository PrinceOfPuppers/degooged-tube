import shelve
import os
import shutil

from degooged_tube.subbox import SubBox, SubBoxChannel, AlreadySubscribed
from degooged_tube.helpers import createPath
import degooged_tube.config as cfg
import degooged_tube.prompts as prompts

from typing import Tuple

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

def loadUserSubbox(username:str) -> Tuple[SubBox, str]:
    channelUrls = []
    channelTags = []

    with shelve.open(f"{cfg.userDataPath}/{username}/data", 'c',writeback=True) as userData:
        subs = userData['subscriptions']
        assert isinstance(subs,dict)
        for channelUrl in subs.keys():
            channelUrls.append(channelUrl)
            channelTags.append(subs[channelUrl]['tags'])

    subbox = SubBox.fromUrls(channelUrls, channelTags)

    # Sanitize Subscriptions
    for channelUrl in channelUrls:
        if channelUrl not in subbox.channelDict.keys():
            if(prompts.yesNoPrompt(f"Issue Loading {channelUrl} \nWould You Like to Unsubscribe from it?")):
                with shelve.open(f"{cfg.userDataPath}/{username}/data", 'c',writeback=True) as userData:
                    removeSubFromUserData(userData['subscriptions'], channelUrl)

                cfg.logger.info(f"Unsubscribed to {channelUrl}")


    return subbox, username
    

def getUsers() -> list[str]:
    if not os.path.exists(cfg.userDataPath):
        return []
    return os.listdir(path=cfg.userDataPath) 

def removeUser(username: str):
    userPath = f'{cfg.userDataPath}/{username}'
    if not os.path.exists(userPath):
        return

    shutil.rmtree(userPath)





###########################
# Subbox State Management #
###########################
def subscribe(username:str, subbox: SubBox, channelUrl:str, tags:set[str]):
    try:
        channel = subbox.addChannelFromUrl(channelUrl, tags)
    except AlreadySubscribed:
        return
    except:
        cfg.logger.error(f"Unable to Subscribe to {channelUrl} \nAre You Sure The URL is Correct?")
        return

    with shelve.open(f"{cfg.userDataPath}/{username}/data", 'c',writeback=True) as userData:
        addSubToUserData(userData['subscriptions'], channelUrl, tags)

    cfg.logger.info(f"Subscribed to {channel.channelName}")




def unsubscribe(username:str, subbox: SubBox, channelUrl: str):
    try:
        channel = subbox.popChannel(subbox.getChannelIndex(channelUrl))
    except KeyError:
        cfg.logger.error(f"Not Subscribed to {channelUrl}")
        return

    with shelve.open(f"{cfg.userDataPath}/{username}/data", 'c',writeback=True) as userData:
        removeSubFromUserData(userData['subscriptions'], channelUrl)

    cfg.logger.info(f"Unsubscribed to {channel.channelName}")


def addTags(username:str, channel: SubBoxChannel, tags: set[str]):
    channel.tags.update(tags)

    with shelve.open(f"{cfg.userDataPath}/{username}/data", 'c',writeback=True) as userData:
        userData['subscriptions'][channel.channelUrl]['tags'].update(tags)


def removeTags(username:str, channel: SubBoxChannel, tags: set[str]):
    for tag in tags:
        channel.tags.discard(tag)

    with shelve.open(f"{cfg.userDataPath}/{username}/data", 'c',writeback=True) as userData:
        for tag in tags:
            userData['subscriptions'][channel.channelUrl]['tags'].discard(tags)


