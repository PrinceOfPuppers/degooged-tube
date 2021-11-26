import configparser
import os
from ntpath import dirname

'''
contains all global variables, also parses config into global variables
'''

_parser = configparser.ConfigParser(allow_no_value=True)
parser.optionxform = str 

def writeToConfig(key,value):
    _parser.set('CONFIG',key,value)
    with open(f'{modulePath}/config.ini', 'w') as configfile:
        _parser.write(configfile)

def _getConfig():
    defaultConfig = {
        'userDataPath': 'userData'
    }
    
    if not os.path.exists(f'{modulePath}/config.ini'):
        _parser['CONFIG'] = defaultConfig
        with open(f'{modulePath}/config.ini','w+') as f:
            _parser.write(f)

    config = _parser['CONFIG']

    for key in defaultConfig.keys():
        if not key in config.keys():
            writeToConfig(key, defaultConfig[key])
            config[key] = defaultConfig[key]

    return config


modulePath = dirname(__file__)
_config = _getConfig()

# global variables
testJsonPath     = f"{modulePath}/tests/testJson"
testDataDumpPath = f"{modulePath}/tests/dataDump.log"
testLogPath = f"{modulePath}/tests/testing.log"
testing = False

integrationTestPath = f"{modulePath}/tests/integrationTests.py"
unitTestPath = f"{modulePath}/tests/unitTest.py"

# config variables
userDataPath = _config['userDataPath']

# logger
import logging
logger = logging.getLogger('degooged_tube')
