from typing import Callable
from degooged_tube.subbox import SubBoxChannel, SubBox
import degooged_tube.config as cfg

class Cancel(Exception):
    pass

def yesNoPrompt(prompt: str):
    answer = input(f'\n{prompt} \n(y)es/(n)o: ').strip().lower()
    if answer == 'y':
        return True
    return False


def listChannels(channels: list[SubBoxChannel]):
    cfg.logger.info('')
    for i,channel in enumerate(channels):
        numPrefix = f'{i}) '
        cfg.logger.info(f'{numPrefix}{channel}')


def qPrompt(initalPrompt: str, inputPrompt: str, onInput: Callable[[str],None], onError: Callable[[str], None] = None, errorType = Exception):
    cfg.logger.info(f"\n{initalPrompt} \nEnter (q) When Finished")

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
            continue

        try:
            onInput(response)

        except errorType:
            onError(response)


def numPrompt(prompt: str, options: list, cancelable:bool = False) -> int:
    cfg.logger.info('')
    for i,option in enumerate(options):
        cfg.logger.info(f'{i}) {option}')
    while True:
        response = input(f'{prompt}' + (', or (c)ancel' if cancelable else '') + ': ').strip().lower()
        if cancelable and response == 'c':
            raise Cancel

        try:
            index = int(response)
        except:
            cfg.logger.error(f"{response} is Not an Integer")
            continue

        if index < 0 or index >= len(options):
            cfg.logger.error(f"{index} is Not an Option")
            continue

        return index
