import sys
import logging
from dataclasses import dataclass
from urllib.parse import quote_plus
from typing import Callable, Tuple, Union
from degooged_tube import pool

import degooged_tube.ytApiHacking as ytapih
import degooged_tube.config as cfg
import degooged_tube.prompts as prompts
from degooged_tube.helpers import getTerminalSize, ignoreReturn
from degooged_tube.subbox import SubBox, SubBoxChannel, ChannelLoadIssue
from degooged_tube.mpvWrapper import playVideo

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
            'Options: (l)ist subs, (n)ew sub, (u)nsubscribe, (a)dd tags, (r)emove tags, (h)ome\n'
            'Option: '
        ).strip().lower()

        options = [
            'l', 'n', 'u', 'a', 'r', 'h'
        ]

        if(len(chosenOption)!= 1 or chosenOption not in options):
            cfg.logger.error(f"{chosenOption} is not an Option")
            continue


        if chosenOption == 'h':
            return

        if chosenOption == 'l':
            cfg.logger.info(f'Subscriptions for {state.username}:')
            prompts.listChannels(state.subbox.channels)
            continue

        if chosenOption == 'n':
            prompts.qPrompt(
                'Enter the URLs of Channels You Want to Subscribe to', 
                'Channel Url', 
                lambda channelUrl: ignoreReturn(
                    cmds.subscribe(state.username, state.subbox, ytapih.sanitizeChannelUrl(channelUrl), set())
                ),
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


def searchPage(state: CliState, searchVideo = True, pageNum: int = 1) -> bool:
    '''return value specifies whether or not to go back to subbox'''
    getPageSize = lambda : int((getTerminalSize()[1] - 5)/2)

    searchTerm = input("Search Term: ")
    sanitizedSearchTerm = quote_plus(searchTerm)

    if searchVideo:
        searchList, filters = ytapih.getSearchVideoList(sanitizedSearchTerm)
    else:
        searchList, filters = ytapih.getSearchChannelList(sanitizedSearchTerm)
        # TODO: filter channel

    searchRes = searchList.getPaginated(pageNum, getPageSize())

    while True:
        searchTitle = f'Search: {searchTerm}, Page: {pageNum}, ' 

        if searchVideo:
            searchTitle += 'Showing Videos:'
        else:
            searchTitle += 'Showing Channels:'


        cfg.logger.info(searchTitle)

        for i,searchItem in enumerate(searchRes):
            cfg.logger.info(f'{i}) {searchItem}')

        # TODO: add subbox tag filtering
        if searchVideo:
            chosenOption = input(
                'Video Options: (w)atch, (r)elated videos, (v)ideo info, (c)hannel info \n'
                'General Options: (p)revious/(n)ext page, (f)ilters, (s)earch, (t)oggle videos/channels, (h)ome, (b)ack\n'
                'Option: '
            ).strip().lower()

            videoOptions   = ['w', 'r', 'v', 'c']
            generalOptions = ['p', 'n', 'f', 's', 't', 'h', 'b']
            options        = videoOptions + generalOptions

            if(len(chosenOption)!= 1 or chosenOption not in options):
                cfg.logger.error(f"{chosenOption} is not an Option")
                continue

            if chosenOption in videoOptions:
                try:
                    index = prompts.numPrompt('Choose a Video Number', searchRes, cancelable = True)
                except prompts.Cancel:
                    continue

                searchVid = searchRes[index]
                assert isinstance(searchVid, ytapih.SearchVideo)

                if chosenOption == 'w':
                    playVideo(searchVid.url)
                    continue

                if chosenOption == 'r':
                    if relatedVideosPage(state, searchVid):
                        return True
                    continue

                if chosenOption == 'v':
                    if videoInfoPage(state, searchVid.url):
                        return True
                    continue

                if chosenOption == 'c':
                    channel = SubBoxChannel.fromUrl(searchVid.channelUrl, set())
                    if channelInfoPage(state, channel):
                        return True
                    continue

        else:
            chosenOption = input(
                'Channel Options: (s)ubscribe/unsubscribe (c)hannel info\n'
                'General Options: (p)revious/(n)ext page, (f)ilters, (s)earch, (t)oggle videos/channels, (h)ome, (b)ack\n'
                'Option: '
            ).strip().lower()

            channelOptions   = ['s', 'c']
            generalOptions = ['p', 'n', 'f', 's', 't', 'h']
            options        = channelOptions + generalOptions

            if(len(chosenOption)!= 1 or chosenOption not in options):
                cfg.logger.error(f"{chosenOption} is not an Option")
                continue

            if chosenOption in channelOptions:
                try:
                    index = prompts.numPrompt('Choose a Channel Number', searchRes, cancelable = True)
                except prompts.Cancel:
                    continue

                searchChannel = searchRes[index]
                assert isinstance(searchChannel, ytapih.SearchChannel)

                if chosenOption == 's':
                    cmds.subscribeUnsubscribe(state.username, state.subbox, searchChannel.channelUrl, searchChannel.channelName)
                    continue

                if chosenOption == 'c':
                    channel = SubBoxChannel.fromUrl(searchChannel.channelUrl, set())
                    if channelInfoPage(state, channel):
                        return True
                    continue

        # general options
        if chosenOption == 'h':
            return True

        if chosenOption == 'b':
            return False

        if chosenOption == 'n':
            pageNum += 1
            searchRes = searchList.getPaginated(pageNum, getPageSize())
            continue

        if chosenOption == 'p':
            if pageNum < 2:
                cfg.logger.error('Already On First Page')
                continue
            pageNum -= 1
            searchRes = searchList.getPaginated(pageNum, getPageSize())
            continue

        if chosenOption == 'f':
            try:
                num = prompts.numPrompt("Select a Filter Catigory", filters, cancelable = True)
            except prompts.Cancel:
                continue

            filterCatigory = filters[num]

            try:
                num = prompts.numPrompt("Select a Filter", filterCatigory.filters, cancelable = True)
            except prompts.Cancel:
                continue

            filter = filterCatigory.filters[num]

            if searchVideo:
                searchList, filters = ytapih.getSearchVideoList(filter.searchUrlFragment)
            else:
                searchList, filters = ytapih.getSearchChannelList(filter.searchUrlFragment)

            pageNum = 0
            searchRes = searchList.getPaginated(pageNum, getPageSize())
            continue


        if chosenOption == 's':
            searchTerm = input("Search Term: ")
            sanitizedSearchTerm = quote_plus(searchTerm)

            if searchVideo:
                searchList, filters = ytapih.getSearchVideoList(sanitizedSearchTerm)
            else:
                searchList, filters = ytapih.getSearchChannelList(sanitizedSearchTerm)

            pageNum = 0
            searchRes = searchList.getPaginated(pageNum, getPageSize())
            continue

        if chosenOption == 't':
            searchVideo = not searchVideo

            if searchVideo:
                searchList, filters = ytapih.getSearchVideoList(sanitizedSearchTerm)
            else:
                searchList, filters = ytapih.getSearchChannelList(sanitizedSearchTerm)

            pageNum = 0
            searchRes = searchList.getPaginated(pageNum, getPageSize())
            continue





def relatedVideosPage(state: CliState, upload: Union[ytapih.Upload, ytapih.SearchVideo, ytapih.VideoInfo]) -> bool:
    '''return value specifies whether or not to go back to subbox'''
    raise NotImplementedError

def commentsPage(state: CliState, commentList: ytapih.YtApiList[str]) -> bool:
    '''return value specifies whether or not to go back to subbox'''
    raise NotImplementedError


def videoInfoPage(state: CliState, videoUrl: str, channel: Union[SubBoxChannel, None] = None) -> bool:
    '''return value specifies whether or not to go back to subbox'''
    videoPage = ytapih.YtInitalPage.fromUrl(videoUrl)

    videoInfo = ytapih.getVideoInfo(videoPage)

    while True:
        likeViewRatio = "N/A" if videoInfo.viewsNum == 0 else (videoInfo.likesNum / videoInfo.viewsNum)

        cfg.logger.info(
            f"Channel Page:\n"
            f"Title:       {videoInfo.title}\n"
            f"Uploader:    {videoInfo.channelName}\n"
            f"UploadDate:  {videoInfo.uploadedOn}\n"
            f"Likes:       {videoInfo.likesNum}\n"
            f"Views:       {videoInfo.viewsNum}\n"
            f"Likes/Views: {likeViewRatio}\n"
            f"Thumbnail:   {videoInfo.thumbnails[0]}\n"
            f"Description: \n{videoInfo.description}\n"
        )


        chosenOption = input(
            'Video Options: (w)atch, (r)elated videos, (c)hannel info, comment (l)ist \n'
            'General Options: (h)ome, (b)ack\n'
            'Option: '
        ).strip().lower()

        options = [
            'w', 'r', 'c', 'l',
            'p', 'n', 'h', 'b'
        ]

        if(len(chosenOption)!= 1 or chosenOption not in options):
            cfg.logger.error(f"{chosenOption} is not an Option")
            continue

        if chosenOption == 'h':
            return True

        if chosenOption == 'b':
            return False

        if chosenOption == 'w':
            playVideo(videoUrl)
            continue

        if chosenOption == 'r':
            if relatedVideosPage(state, videoInfo):
                return True
            continue

        if chosenOption == 'c':
            if channel is None:
                channel = SubBoxChannel.fromUrl(videoInfo.channelUrl, set())
            if channelInfoPage(state, channel):
                return True
            continue

        if chosenOption == 'l':
            commentList = ytapih.getCommentList(videoPage)
            if commentsPage(state, commentList):
                return True
            continue

        raise Exception(f'Reached End Of VideoInfo Switch, Option Chosen {chosenOption}, This Should Never Occur')


def channelInfoPage(state: CliState, channel: SubBoxChannel) -> bool:
    '''return value specifies whether or not to go back to subbox'''
    while True:
        cfg.logger.info(
            f"Channel Page:\n"
            f"Name:          {channel.channelName}\n"
            f"Url:           {channel.channelUrl}\n"
            f"Subscribers:   {channel.channelInfo.subscribers}\n"
            f"Avatar:        {channel.channelInfo.avatar[0]}\n"
            f"Banner:        {channel.channelInfo.banners[0]}\n"
            f"Description: \n{channel.channelInfo.description}\n"
        )
        
        chosenOption = input(
            'Options: (u)ploads, (h)ome, (b)ack\n'
            'Option: '
        ).strip().lower()

        options = [
            'h', 'u', 'b'
        ]

        if(len(chosenOption)!= 1 or chosenOption not in options):
            cfg.logger.error(f"{chosenOption} is not an Option")
            continue

        if chosenOption == 'h':
            return True

        if chosenOption == 'b':
            return False

        if chosenOption == 'u':
            if uploadsPage(state, channel):
                return True
            continue


def uploadsPage(state: CliState, channel: SubBoxChannel, pageNum: int = 1) -> bool:
    '''return value specifies whether or not to go back to subbox'''
    getPageSize = lambda : int((getTerminalSize()[1] - 4)/3)

    uploads = channel.uploadList.getPaginated(pageNum, getPageSize())

    while True:
        cfg.logger.info(f"Uploads Page {pageNum} of {channel.channelName}")

        for i,upload in enumerate(uploads):
            cfg.logger.info(f'{i}) {upload}')

        chosenOption = input(
            'Video Options: (w)atch, (r)elated videos, (v)ideo info, (c)hannel info \n'
            'General Options: (p)revious/(n)ext page, (h)ome, (b)ack\n'
            'Option: '
        ).strip().lower()

        options = [
            'w', 'r', 'v', 'c', 
            'p', 'n', 'h', 'b'
        ]

        if(len(chosenOption)!= 1 or chosenOption not in options):
            cfg.logger.error(f"{chosenOption} is not an Option")
            continue
        # general options
        if chosenOption == 'h':
            return True

        if chosenOption == 'b':
            return False

        # general options
        if chosenOption == 'n':
            pageNum += 1
            uploads = channel.uploadList.getPaginated(pageNum, getPageSize())
            continue

        if chosenOption == 'p':
            if pageNum < 2:
                cfg.logger.error('Already On First Page')
                continue
            pageNum -= 1
            uploads = channel.uploadList.getPaginated(pageNum, getPageSize())
            continue

        # video options
        try:
            index = prompts.numPrompt('Choose a Video Number',uploads, cancelable = True)
        except prompts.Cancel:
            continue

        upload = uploads[index]

        if chosenOption == 'w':
            playVideo(upload.url)
            continue

        if chosenOption == 'r':
            if relatedVideosPage(state, upload):
                return True
            continue

        if chosenOption == 'v':
            if videoInfoPage(state, upload.url):
                return True

            continue

        if chosenOption == 'c':
            if channelInfoPage(state, channel):
                return True
            continue

        raise Exception(f'Reached End Of uploadPage Switch, Option Chosen {chosenOption}, Index {index}\n This Should Never Occur')



def subboxPage(state: CliState, pageNum: int = 1, tags:Union[set[str], None] = None):
    getPageSize = lambda : int((getTerminalSize()[1] - 4)/3)

    uploads = state.subbox.getPaginatedUploads(pageNum, getPageSize(), tags)

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
            uploads = state.subbox.getPaginatedUploads(pageNum, getPageSize(), tags)
            continue

        if chosenOption == 'p':
            if pageNum < 2:
                cfg.logger.error('Already On First Page')
                continue
            pageNum -= 1
            uploads = state.subbox.getPaginatedUploads(pageNum, getPageSize(), tags)
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
            searchPage(state)
            continue

        if chosenOption == 'e':
            subscriptionsPage(state)
            continue

        if chosenOption == 'l':
            state.subbox, state.username = loginPage(autoLogin = False)
            continue


        # video options
        try:
            index = prompts.numPrompt('Choose a Video Number',uploads, cancelable = True)
        except prompts.Cancel:
            continue

        upload = uploads[index]

        if chosenOption == 'w':
            playVideo(upload.url)
            continue

        if chosenOption == 'r':
            relatedVideosPage(state, upload):
            continue

        if chosenOption == 'v':
            videoInfoPage(state, upload.url)
            continue

        if chosenOption == 'c':
            channelInfoPage(state, state.subbox.channelDict[upload.channelUrl])
            continue

        raise Exception(f'Reached End Of SubBoxPage Switch, Option Chosen {chosenOption}, Index {index}\n This Should Never Occur')




def cli():
    setupLogger()

    subbox, username = loginPage()
    state = CliState(subbox, username)
    subboxPage(state)
