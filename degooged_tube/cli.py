import sys
import logging
from dataclasses import dataclass

import degooged_tube.ytApiHacking as ytapih
import degooged_tube.config as cfg
import degooged_tube.prompts as prompts
from degooged_tube.helpers import getTerminalSize
from degooged_tube.subbox import SubBox, SubBoxChannel
from degooged_tube.mpvWrapper import playVideo

from typing import Callable, Tuple, Union

import degooged_tube.commands as cmds

def setupLogger():
    stream = logging.StreamHandler(sys.stdout)
    cfg.logger.setLevel(logging.INFO)
    stream.setFormatter(logging.Formatter("%(message)s"))
    cfg.logger.addHandler(stream)



def createNewUserPrompt():
    username = input("No Users Found, Please Enter a New Username: ")

    if(not prompts.yesNoPrompt('Would you Like add Subscriptions Now? \n(can be done later)')):
        return cmds.createNewUser(username)

    channels = []
    prompts.qPrompt(
        'Enter the URLs of Channels You Want to Subscribe to', 
        'Channel Url', 
        lambda channelUrl: channels.append(ytapih.sanitizeChannelUrl(channelUrl))
    )

    subbox = cmds.createNewUser(username, channels)
    if(not prompts.yesNoPrompt('Would You Like to Tag Any of These Channels? \n(tags can be used to filter subbox, can be added later)')):
        return subbox

    prompts.listChannels(subbox.channels)

    def callback(response: str):
        try:
            index = int(response)
        except:
            cfg.logger.error(f"{response} is Not an Integer")
            return

        if index < 0 or index >= len(channels):
            cfg.logger.error("Number Not in List")
            return

        tags = input('Space Seperated Tags: ')
        tags = tags.split()

        channel = subbox.channels[index]

        for tag in tags:
            channel.tags.add(tag.strip())

        prompts.listChannels(subbox.channels)


    prompts.qPrompt(
        'Enter the Number of the Channel From the Above List', 
        'Channel Number', 
        callback
    )
    
    cfg.logger.info("\nUser Created!")
    return subbox






#############
# CLI Pages #
#############

@dataclass
class CliState:
    subbox:SubBox


def loginPage():
    users = cmds.getUsers()
    if len(users) == 0:
        return createNewUserPrompt()
    if len(users) == 1:
        return cmds.loadUserSubbox(users[0])

    return cmds.loadUserSubbox(users[prompts.numPrompt('Pick a User Number', users)])


def subscriptionsPage(state: CliState):
    raise NotImplementedError


def searchPage(state: CliState):
    raise NotImplementedError


def relatedVideosPage(state: CliState, upload: ytapih.Upload):
    raise NotImplementedError


def videoInfoPage(state: CliState, upload: ytapih.Upload):
    raise NotImplementedError


def channelInfoPage(state: CliState, channel: SubBoxChannel):
    raise NotImplementedError


def subboxPage(state: CliState, pageNum: int = 1, tags:Union[set[str], None] = None) -> Tuple[Callable, list]:
    _, termHeight = getTerminalSize()
    pageSize = int(termHeight/2 - 2)

    uploads = state.subbox.getPaginatedUploads(pageNum, pageSize, tags)

    while True:
        cfg.logger.info(f'Subbox Page {pageNum}:')
        for i,upload in enumerate(uploads):
            cfg.logger.info(f'{i}) {upload}')

        # TODO: add subbox tag filtering
        chosenOption = input(
            '\n'
            'Video Options: (w)atch, (r)elated videos, (v)ideo info, (c)hannel info \n'
            'General Options: (p)revious/(n)ext page, (f)ilter by tag, (s)earch, (e)dit subs, (l)ogout\n'
            'Option: '
        ).strip().lower()

        options = [
            'w', 'r', 'v', 'c', 
            'p', 'n', 'f', 's', 'e', 'l'
        ]

        if(len(chosenOption)!= 1 or chosenOption not in options):
            cfg.logger.error(f"{chosenOption} is not an Option")
            continue


        # general options
        if chosenOption == 'n':
            pageNum += 1
            _, termHeight = getTerminalSize()
            pageSize = int(termHeight/2 - 3)
            uploads = state.subbox.getPaginatedUploads(pageNum, pageSize, tags)
            continue

        if chosenOption == 'p':
            if pageNum < 2:
                cfg.logger.error('Already On First Page')
                continue
            pageNum -= 1
            _, termHeight = getTerminalSize()
            pageSize = int(termHeight/2 - 2)
            uploads = state.subbox.getPaginatedUploads(pageNum, pageSize, tags)
            continue

        if chosenOption == 'f':
            t = set()
            allTags = state.subbox.getAllTags()
            if len(allTags) == 0:
                input('\nNo Channels are Currently Tagged \nHit Enter to Go Back To Subbox: ')
                continue

            cfg.logger.info(f"\n Channel Tags: {allTags}")

            def onInput(r):
                if r not in allTags:
                    raise Exception()
                t.add(r)

            def onError(r):
                cfg.logger.error(f'No Tag: {r} in Channel Tags {allTags}')

            prompts.qPrompt(
                'Enter Tags to Filter By',
                'Tag',
                onInput,
                onError= onError
            )

        if chosenOption == 's':
            return searchPage, []

        if chosenOption == 'e':
            return subscriptionsPage, []

        if chosenOption == 'l':
            state.subbox = loginPage()
            return subboxPage, [1, None]


        # video options
        try:
            index = prompts.numPrompt('Choose a Video Number',uploads, cancelable = True)
        except prompts.Cancel:
            continue

        upload = uploads[index]

        if chosenOption == 'w':
            playVideo(upload.url)
            return subboxPage, [pageNum, tags]

        if chosenOption == 'r':
            relatedVideosPage(state, upload)
            return subboxPage, [pageNum, tags]

        if chosenOption == 'v':
            videoInfoPage(state, upload)
            return subboxPage, [pageNum, tags]

        if chosenOption == 'c':
            channelInfoPage(state, state.subbox.channelDict[upload.channelUrl])
            return subboxPage, [pageNum, tags]

        raise Exception(f'Reached End Of SubBoxPage Switch, Option Chosen {chosenOption}, Index {index}\n This Should Never Occur')




def cli():
    setupLogger()

    subbox = loginPage()
    state = CliState(subbox)

    page:Callable = subboxPage
    args = [1, None]

    while True:
        page, args = page(state, *args)
        

