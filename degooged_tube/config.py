import configparser
import os
from ntpath import dirname

'''
contains all global variables, also parses config into global variables
'''

_parser = configparser.ConfigParser(allow_no_value=True)
_parser.optionxform = str 

def writeToConfig(key,value):
    _parser.set('CONFIG',key,value)
    with open(f'{modulePath}/config.ini', 'w') as configfile:
        _parser.write(configfile)

def _getConfig():
    defaultConfig = {
        'userDataPath': 'userData',
        'maxQuality': 'best',
        'maxFps': 'highest'
    }
    cfgPath = f'{modulePath}/config.ini'

    if not os.path.exists(cfgPath):
        _parser['CONFIG'] = defaultConfig
        with open(cfgPath, 'w+') as f:
            _parser.write(f)
    else:
        _parser.read(cfgPath)
    

    config = _parser['CONFIG']

    for key in defaultConfig.keys():
        if not key in config.keys():
            writeToConfig(key, defaultConfig[key])
            config[key] = defaultConfig[key]

    return config


modulePath = dirname(__file__)
_config = _getConfig()

# global constants
testJsonPath     = f"{modulePath}/tests/testJson"
testDataDumpPath = f"{modulePath}/tests/dataDump.log"
testLogPath = f"{modulePath}/tests/testing.log"
integrationTestPath = f"{modulePath}/tests/integrationTests.py"
unitTestPath = f"{modulePath}/tests/unitTest.py"

# global variables
testing = False

availableFps = [
    '30', '60', 'highest'
]

availableQualities = [
        '144',
        '240',
        '360',
        '480',
        '720',
        '1080',
        'best'
]

# config variables
userDataPath = f"{modulePath}/{_config['userDataPath']}"
maxQuality = _config['maxQuality']
maxFps = _config['maxFps']

# logger
import logging
logger = logging.getLogger('degooged_tube')
