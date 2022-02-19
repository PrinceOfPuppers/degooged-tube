import sys
import logging
from dataclasses import dataclass
from urllib.parse import quote_plus
from typing import Callable, Tuple, Union
from degooged_tube import pool, setupPool

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
            'Options: (l)ist subs, (s)ubscribe, (u)nsubscribe, (a)dd tags, (r)emove tags, (h)ome\n'
            'Option: '
        ).strip().lower()

        options = [
            'l', 's', 'u', 'a', 'r', 'h'
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

        if chosenOption == 's':
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


def _searchVideoHelper(state: CliState, searchVid: ytapih.SearchVideo) -> bool:
    '''return value specifies whether or not to go back to subbox'''
    while True:
        cfg.logger.info(f"Video Selected: \n{searchVid}")
        chosenOption = input(
            'Video Options: (w)atch, (r)elated videos, (v)ideo info, (c)hannel info (b)ack\n'
            'Option: '
        ).strip().lower()

        options        = ['w', 'r', 'v', 'c', 'b']

        if(len(chosenOption)!= 1 or chosenOption not in options):
            cfg.logger.error(f"{chosenOption} is not an Option")
            continue
        break
        

    if chosenOption == 'b':
        return False

    if chosenOption == 'w':
        playVideo(searchVid.url)
        return False

    if chosenOption == 'r':
        videoPage = ytapih.YtInitalPage.fromUrl(searchVid.url)
        if relatedVideosPage(state, videoPage, searchVid.title):
            return True
        return False

    if chosenOption == 'v':
        if videoInfoPage(state, searchVid.url):
            return True
        return False

    if chosenOption == 'c':
        channel = SubBoxChannel.fromUrl(searchVid.channelUrl, set())
        if channelInfoPage(state, channel):
            return True
        return False

    raise Exception(f'Reached End Of SearchVideoHelper Switch, Option Chosen {chosenOption}')


def _searchChannelHelper(state: CliState, searchChannel) -> bool:
    '''return value specifies whether or not to go back to subbox'''
    while True:
        chosenOption = input(
            'Options: (s)ubscribe/unsubscribe (c)hannel info, (b)ack\n'
            'Option: '
        ).strip().lower()

        options   = ['s', 'c', 'b']

        if(len(chosenOption)!= 1 or chosenOption not in options):
            cfg.logger.error(f"{chosenOption} is not an Option")
            continue
        break

    if chosenOption == 's':
        cmds.subscribeUnsubscribe(state.username, state.subbox, searchChannel.channelUrl, searchChannel.channelName)
        return False

    if chosenOption == 'c':
        channel = SubBoxChannel.fromUrl(searchChannel.channelUrl, set())
        if channelInfoPage(state, channel):
            return True
        return False
    raise Exception(f'Reached End Of SearchChannelHelper Switch, Option Chosen {chosenOption}')


def searchPage(state: CliState, pageNum: int = 1) -> bool:
    '''return value specifies whether or not to go back to subbox'''
    getPageSize = lambda : int((getTerminalSize()[1] - 5)/3)

    searchTerm = input("Search Term: ")
    sanitizedSearchTerm = quote_plus(searchTerm)
    searchList, filters = ytapih.getSearchList(sanitizedSearchTerm)

    searchRes = searchList.getPaginated(pageNum, getPageSize())

    while True:
        searchTitle = f'Search: {searchTerm}, Page: {pageNum}' 

        cfg.logger.info(searchTitle)

        for i,searchItem in enumerate(searchRes):
            cfg.logger.info(f'{i}) {searchItem}')

        chosenOption = input(
            'List Options: (c)hoose item\n'
            'General Options: (p)revious/(n)ext page, (f)ilters, (s)earch, (h)ome, (b)ack\n'
            'Option: '
        ).strip().lower()

        listOptions   = ['c']
        generalOptions = ['p', 'n', 'f', 's', 'h', 'b']
        options        = listOptions + generalOptions

        if(len(chosenOption)!= 1 or chosenOption not in options):
            cfg.logger.error(f"{chosenOption} is not an Option")
            continue

        if chosenOption in listOptions:
            try:
                index = prompts.numPrompt('Choose an Item Number', searchRes, cancelable = True)
            except prompts.Cancel:
                continue

            searchItem = searchRes[index]

            if isinstance(searchItem, ytapih.SearchVideo):
                if _searchVideoHelper(state, searchItem):
                    return True
                continue
            elif isinstance(searchItem, ytapih.SearchChannel):
                if _searchChannelHelper(state, searchItem):
                    return True
                continue
            else:
                raise Exception("This Should Never Occur")

        elif chosenOption in generalOptions:
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

                searchList, filters = ytapih.getSearchList(filter.searchUrlFragment)

                pageNum = 0
                searchRes = searchList.getPaginated(pageNum, getPageSize())
                continue


            if chosenOption == 's':
                searchTerm = input("Search Term: ")
                sanitizedSearchTerm = quote_plus(searchTerm)

                searchList, filters = ytapih.getSearchList(sanitizedSearchTerm)

                pageNum = 0
                searchRes = searchList.getPaginated(pageNum, getPageSize())
                continue

            raise Exception(f'Reached End Of SearchPage Switch, Option Chosen {chosenOption}')





def relatedVideosPage(state: CliState, videoPage: ytapih.YtInitalPage, videoTitle:str, pageNum:int = 1) -> bool:
    '''return value specifies whether or not to go back to subbox'''
    getPageSize = lambda : int((getTerminalSize()[1] - 4)/3)

    relatedVideoList = ytapih.getRelatedVideoList(videoPage)
    relatedVideos = relatedVideoList.getPaginated(pageNum, getPageSize())

    while True:
        cfg.logger.info(f"Related Videos Page {pageNum} for Video: {videoTitle}")

        for i,relatedVideo in enumerate(relatedVideos):
            cfg.logger.info(f'{i}) {relatedVideo}')

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
            relatedVideos = relatedVideoList.getPaginated(pageNum, getPageSize())
            continue

        if chosenOption == 'p':
            if pageNum < 2:
                cfg.logger.error('Already On First Page')
                continue
            pageNum -= 1
            relatedVideos = relatedVideoList.getPaginated(pageNum, getPageSize())
            continue

        # video options
        try:
            index = prompts.numPrompt('Choose a Video Number',relatedVideos, cancelable = True)
        except prompts.Cancel:
            continue

        relatedVideo = relatedVideos[index]

        if chosenOption == 'w':
            playVideo(relatedVideo.url)
            continue

        if chosenOption == 'r':
            videoPage = ytapih.YtInitalPage.fromUrl(relatedVideo.url)
            if relatedVideosPage(state, videoPage, relatedVideo.title):
                return True
            continue

        if chosenOption == 'v':
            if videoInfoPage(state, relatedVideo.url):
                return True

            continue

        if chosenOption == 'c':
            channel = SubBoxChannel.fromUrl(relatedVideo.channelUrl, set())
            if channelInfoPage(state, channel):
                return True
            continue

        raise Exception(f'Reached End Of uploadPage Switch, Option Chosen {chosenOption}, Index {index}\n This Should Never Occur')


def commentsPage(state: CliState, commentList: ytapih.YtApiList[str], videoTitle: str, pageNum:int = 1) -> bool:
    '''return value specifies whether or not to go back to subbox'''
    getPageSize = lambda : int((getTerminalSize()[1] - 3)/4)

    comments = commentList.getPaginated(pageNum, getPageSize())

    while True:
        cfg.logger.info(f"Comments Page {pageNum} of Video: {videoTitle}")

        for i,comment in enumerate(comments):
            cfg.logger.info(f'{i}) {comment}\n')

        chosenOption = input(
            'Options: (p)revious/(n)ext page, (h)ome, (b)ack\n'
            'Option: '
        ).strip().lower()

        options = [
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
            comments = commentList.getPaginated(pageNum, getPageSize())
            continue

        if chosenOption == 'p':
            if pageNum < 2:
                cfg.logger.error('Already On First Page')
                continue
            pageNum -= 1
            comments = commentList.getPaginated(pageNum, getPageSize())
            continue

        raise Exception(f'Reached End Of commentPage Switch, Option Chosen {chosenOption}, This Should Never Occur')



def videoInfoPage(state: CliState, videoUrl: str, channel: Union[SubBoxChannel, None] = None) -> bool:
    '''return value specifies whether or not to go back to subbox'''
    videoPage = ytapih.YtInitalPage.fromUrl(videoUrl)

    videoInfo = ytapih.getVideoInfo(videoPage)
    if videoInfo is None:
        cfg.logger.info("Error getting Video Info")
        return False

    while True:
        likeViewRatio = "N/A" if videoInfo.viewsNum == 0 else (videoInfo.likesNum / videoInfo.viewsNum)

        cfg.logger.info(
            f"Video Info:\n"
            f"Title:       {videoInfo.title}\n"
            f"Uploader:    {videoInfo.channelName}\n"
            f"Avatar:      {'' if len(videoInfo.avatar) == 0 else videoInfo.avatar[-1]}\n"
            f"UploadDate:  {videoInfo.uploadedOn}\n"
            f"Likes:       {videoInfo.likesNum}\n"
            f"Views:       {videoInfo.viewsNum}\n"
            f"Likes/Views: {likeViewRatio}\n"
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
            if relatedVideosPage(state, videoPage, videoInfo.title):
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
            if commentsPage(state, commentList, videoInfo.title):
                return True
            continue

        raise Exception(f'Reached End Of VideoInfo Switch, Option Chosen {chosenOption}, This Should Never Occur')


def channelInfoPage(state: CliState, channel: SubBoxChannel) -> bool:
    '''return value specifies whether or not to go back to subbox'''
    while True:
        avatar = "" if len(channel.channelInfo.avatar) == 0 else channel.channelInfo.avatar[-1]
        banner = "" if len(channel.channelInfo.banners) == 0 else channel.channelInfo.banners[-1]
        cfg.logger.info(
            f"Channel Page:\n"
            f"Name:          {channel.channelName}\n"
            f"Url:           {channel.channelUrl}\n"
            f"Subscribers:   {channel.channelInfo.subscribers}\n"
            f"Avatar:        {avatar}\n"
            f"Banner:        {banner}\n"
            f"Description: \n{channel.channelInfo.description}\n"
        )
        
        chosenOption = input(
            'Options: (u)ploads, (s)ubscribe/unsubscribe, (h)ome, (b)ack\n'
            'Option: '
        ).strip().lower()

        options = [
            'h', 'u', 's', 'b'
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

        if chosenOption == 's':
            cmds.subscribeUnsubscribe(state.username, state.subbox, channel.channelUrl, channel.channelName)
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
            'Video Options: (w)atch, (r)elated videos, (v)ideo info\n'
            'General Options: (p)revious/(n)ext page, (c)hannel info, (h)ome, (b)ack\n'
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

        if chosenOption == 'c':
            if channelInfoPage(state, channel):
                return True
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
            videoPage = ytapih.YtInitalPage.fromUrl(upload.url)
            if relatedVideosPage(state, videoPage, upload.title):
                return True
            continue

        if chosenOption == 'v':
            if videoInfoPage(state, upload.url):
                return True

            continue

        raise Exception(f'Reached End Of uploadPage Switch, Option Chosen {chosenOption}, Index {index}\n This Should Never Occur')



def subboxPage(state: CliState, pageNum: int = 1, tags:Union[set[str], None] = None):
    getPageSize = lambda : int((getTerminalSize()[1] - 4)/3)

    if tags is None:
        tags = set()


    while True:
        uploads = state.subbox.getPaginated(pageNum, getPageSize(), tags)

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
            'General Options: (p)revious/(n)ext page, (r)efresh, (f)ilter by tag, (s)earch, (e)dit subs, (l)ogout\n'
            'Option: '
        ).strip().lower()

        options = [
            'w', 'r', 'v', 'c', 
            'p', 'n', 'r', 'f', 's', 'e', 'l'
        ]

        if(len(chosenOption)!= 1 or chosenOption not in options):
            cfg.logger.error(f"{chosenOption} is not an Option")
            continue

        # general options
        if chosenOption == 'n':
            pageNum += 1
            #uploads = state.subbox.getPaginated(pageNum, getPageSize(), tags)
            continue

        if chosenOption == 'p':
            if pageNum < 2:
                cfg.logger.error('Already On First Page')
                continue
            pageNum -= 1
            #uploads = state.subbox.getPaginated(pageNum, getPageSize(), tags)
            continue

        if chosenOption == 'r':
            pageNum = 1
            state.subbox.reload()
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

            tags.clear()
            tags.update(t)
            uploads = state.subbox.getPaginated(pageNum, getPageSize(), tags)
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
            videoPage = ytapih.YtInitalPage.fromUrl(upload.url)
            relatedVideosPage(state, videoPage, upload.title)
            continue

        if chosenOption == 'v':
            videoInfoPage(state, upload.url)
            continue

        if chosenOption == 'c':
            channelInfoPage(state, state.subbox.channelDict[upload.channelUrl])
            continue

        raise Exception(f'Reached End Of SubBoxPage Switch, Option Chosen {chosenOption}, Index {index}\n This Should Never Occur')




def cli():
    #cfg.testing = True
    setupLogger()
    setupPool()

    subbox, username = loginPage()
    state = CliState(subbox, username)
    subboxPage(state)
