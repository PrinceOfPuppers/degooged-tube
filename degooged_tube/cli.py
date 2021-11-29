import sys
import logging
from dataclasses import dataclass

import degooged_tube.ytApiHacking as ytapih
import degooged_tube.config as cfg
import degooged_tube.prompts as prompts
from degooged_tube.helpers import getTerminalSize
from degooged_tube.subbox import SubBox, SubBoxChannel, ChannelLoadIssue
from degooged_tube.mpvWrapper import playVideo

from typing import Callable, Tuple, Union

import degooged_tube.commands as cmds

def setupLogger():
    stream = logging.StreamHandler(sys.stdout)
    cfg.logger.setLevel(logging.INFO)
    stream.setFormatter(logging.Formatter("%(message)s"))
    cfg.logger.addHandler(stream)


def createNewUserPrompt() -> Tuple[SubBox, str]:
    while True:
        username = input("Enter a New Username: ")
        existingUsers = cmds.getUsers()
        if username in existingUsers:
            cfg.logger.error(f"Username: {username} is taken")
            continue
        break


    if(not prompts.yesNoPrompt('Would you Like add Subscriptions Now? \n(can be done later)')):
        return cmds.createNewUser(username), username

    channels = []
    prompts.qPrompt(
        'Enter the URLs of Channels You Want to Subscribe to', 
        'Channel Url', 
        lambda channelUrl: channels.append(ytapih.sanitizeChannelUrl(channelUrl)),
        lambda channelUrl: cfg.logger.error(f"Unable to Subscribe to {channelUrl}\n Are You Sure the URL is Correct?"),
        ChannelLoadIssue
    )

    subbox = cmds.createNewUser(username, channels)
    if(not prompts.yesNoPrompt('Would You Like to Tag Any of These Channels? \n(tags can be used to filter subbox, can be added later)')):
        return subbox, username

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
        tags = set(tags.split())

        channel = subbox.channels[index]

        cmds.addTags(username, channel, tags)

        prompts.listChannels(subbox.channels)


    prompts.qPrompt(
        'Enter the Number of the Channel From the Above List', 
        'Channel Number', 
        callback
    )
    
    return subbox, username






#############
# CLI Pages #
#############

@dataclass
class CliState:
    subbox:SubBox
    username:str


def loginPage(autoLogin:bool = True) -> Tuple[SubBox, str]:
    users = cmds.getUsers()

    while True:
        if len(users) == 0:
            cfg.logger.info("\nNo Existing Users Detected, Creating New User")
            return createNewUserPrompt()

        if len(users) == 1 and autoLogin:
            return cmds.loadUserSubbox(users[0])
        
        if autoLogin:
            cfg.logger.info('Login: ')
            return cmds.loadUserSubbox(users[prompts.numPrompt('Pick a User Number', users)])

        optionChosen = input('\n(l)ogin, (n)ew user, (r)emove user\nSelect an Option: ').strip().lower()
        if optionChosen not in ['l', 'n', 'r']:
            cfg.logger.error(f'{optionChosen} is Not an Option')
            continue

        if optionChosen == 'l':
            return cmds.loadUserSubbox(users[prompts.numPrompt('Pick a User Number', users)])

        if optionChosen == 'n':
            return createNewUserPrompt()

        if optionChosen == 'r':
            index = prompts.numPrompt('Pick a User Number to Remove', users)
            u = users[index]
            if(not prompts.yesNoPrompt(f'Are You Sure You Want to Permanently Remove User: {u}')):
                continue

            cmds.removeUser(u)
            cfg.logger.info(f'{u} Removed!')
            users = cmds.getUsers()
            continue


def subscriptionsPage(state: CliState):
    while True:
        cfg.logger.info('\nEdit Subscriptions:')
        chosenOption = input(
            'Options: (l)ist subs, (n)ew sub, (u)nsubscribe, (a)dd tags, (r)emove tags, (q) to return\n'
            'Option: '
        ).strip().lower()

        options = [
            'l', 'n', 'u', 'a', 'r', 'q'
        ]

        if(len(chosenOption)!= 1 or chosenOption not in options):
            cfg.logger.error(f"{chosenOption} is not an Option")
            continue


        if chosenOption == 'q':
            return

        if chosenOption == 'l':
            cfg.logger.info(f'Subscriptions for {state.username}:')
            prompts.listChannels(state.subbox.channels)
            continue

        if chosenOption == 'n':
            prompts.qPrompt(
                'Enter the URLs of Channels You Want to Subscribe to', 
                'Channel Url', 
                lambda channelUrl: cmds.subscribe(state.username, state.subbox, ytapih.sanitizeChannelUrl(channelUrl), set()),
                lambda channelUrl: cfg.logger.error(f"Unable to Subscribe to {channelUrl}, Are You Sure the URL is Correct?"),
                ChannelLoadIssue
            )
            continue

        if chosenOption == 'u':
            try: 
                index = prompts.numPrompt(
                    'Enter the Number of the Channel to Unsubscribe to it',
                    state.subbox.channels,
                    cancelable = True
                )
            except prompts.Cancel:
                continue
            cmds.unsubscribe(state.username, state.subbox, ytapih.sanitizeChannelUrl(state.subbox.channels[index].channelUrl))
            continue

        if chosenOption == 'a':
            try: 
                index = prompts.numPrompt(
                    'Enter the Number of the Channel You Want to Add Tags to',
                    state.subbox.channels,
                    cancelable = True
                )
            except prompts.Cancel:
                continue

            channel = state.subbox.channels[index]
            tags = input('Space Seperated Tags: ')
            tags = set(tags.split())
            cmds.addTags(state.username, channel, tags)
            cfg.logger.info(f'Tags: {tags} Have Been Added to {channel.channelName}')
            continue

        if chosenOption == 'r':
            try: 
                index = prompts.numPrompt(
                    'Enter the Number of the Channel you Wish to Remove Tags From',
                    state.subbox.channels,
                    cancelable = True
                )
            except prompts.Cancel:
                continue

            channel = state.subbox.channels[index]
            tags = input('Space Seperated Tags: ')
            tags = set(tags.split())
            cmds.removeTags(state.username, channel, tags)
            cfg.logger.info(f'Tags: {tags} Have Been Removed from {channel.channelName}')
            continue




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

        if tags != None and len(tags) > 0:
            subboxTitle = f'Subbox Page {pageNum}, Tags: {tags}:' 
        else:
            subboxTitle = f'Subbox Page {pageNum}:' 

        cfg.logger.info(subboxTitle)
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

            tags = t
            continue

        if chosenOption == 's':
            return searchPage, []

        if chosenOption == 'e':
            subscriptionsPage(state)
            continue

        if chosenOption == 'l':
            state.subbox, state.username = loginPage(autoLogin = False)
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

    subbox, username = loginPage()
    state = CliState(subbox, username)

    page:Callable = subboxPage
    args = [1, None]

    while True:
        page, args = page(state, *args)
        

