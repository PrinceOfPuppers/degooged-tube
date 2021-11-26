import sys
import logging

import degooged_tube.ytApiHacking as ytapih
import degooged_tube.config as cfg
import degooged_tube.prompts as prompts

import commands as cmds

def setupLogger():
    stream = logging.StreamHandler(sys.stdout)
    cfg.logger.setLevel(logging.DEBUG)
    stream.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    cfg.logger.addHandler(stream)


def createNewUserPrompt():
    username = input("No Users Found, Please Enter a New Username: ")

    if(not prompts.yesNoPrompt('Would you Like add Subscriptions Now? \n(can be done later)')):
        return cmds.createNewUser(username)

    cfg.logger.info("Enter the URLS of Channels You Want to Subscribe to, Hitting (Enter) After Each. \n Enter (q) When Finished")

    channels = []
    prompts.qPrompt(
        'Enter the URLs of Channels You Want to Subscribe to, Hitting (Enter) After Each', 
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

        channel = channels[index]

        for tag in tags:
            channel.tags.add(tag.strip())

        prompts.listChannels(subbox.channels)


    prompts.qPrompt(
        'Enter the Number of the Channel From the Above List', 
        'Channel Number', 
        callback
    )
    
    cfg.logger.info("User Created!")


def startup():
    users = cmds.getUsers()
    if len(users) == 0:
        return createNewUserPrompt()
    if len(users) == 1:
        return cmds.loadUserSubbox(users[0])

    while(True):
        try:
            return cmds.loadUserSubbox(users[prompts.numPrompt('Pick a User Number', users)])
        except IndexError:
            pass
    
def cli():
    setupLogger()
    subbox = startup()
    


