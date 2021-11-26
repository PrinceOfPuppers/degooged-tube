from typing import Callable
from degooged_tube.subbox import SubBoxChannel
import degooged_tube.config as cfg

def yesNoPrompt(prompt: str):
    answer = input(f'{prompt} \n(y)es/(n)o: ').strip().lower()
    if answer == 'y':
        return True
    return False


def listChannels(channels: list[SubBoxChannel]):
    for i,channel in enumerate(channels):
        try:
            label = channel.scrapedData['name']
        except KeyError:
            label = channel.channelUrl

        cfg.logger.info(f'{i}) {label}\n  tags:{channel.tags}')


def qPrompt(initalPrompt: str, inputPrompt: str, onInput: Callable[[str],None], onError: Callable[[str], None] = None):
    cfg.logger.info(f"{initalPrompt}\n Enter (q) When Finished")

    while True:
        response = input(f'{inputPrompt}: ')
        response.strip()
        if response == 'q' or response == 'Q':
            break
        if len(response) == 0:
            cfg.logger.info("Enter (q) if You're Finished")
            continue
        
        if onError is None:
            onInput(response)
            return

        try:
            onInput(response)
        except:
            onError(response)

def numPrompt(prompt: str, options: list[str]) -> int:
    for i,option in options:
        cfg.logger.info(f'{i}) {option}')
    response = input(f'{prompt}: ').strip()

    try:
        index = int(response)
    except:
        cfg.logger.error(f"{response} is Not an Integer")
        raise IndexError

    if index < 0 or index >= len(options):
        cfg.logger.error(f"{index} is Not an Option")
        raise IndexError

    return index
