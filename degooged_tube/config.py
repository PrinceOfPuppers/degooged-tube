import configparser
import os
from ntpath import dirname

'''
contains all global variables, also parses config into global variables
'''

def createDefaultConfig(parser):
    defaultConfig = {
        # 'musicDir' : '',
    }

    parser['CONFIG'] = defaultConfig
    with open(f'{modulePath}/config.ini','w+') as f:
        parser.write(f)
    
def writeToConfig(key,value):
    parser.set('CONFIG',key,value)
    with open(f'{modulePath}/config.ini', 'w') as configfile:
        parser.write(configfile)

modulePath = dirname(__file__)

#loading config
parser = configparser.ConfigParser(allow_no_value=True)
parser.optionxform = str 

if not os.path.exists(f'{modulePath}/config.ini'):
    createDefaultConfig(parser)

else:
    parser.read(f'{modulePath}/config.ini')


section = parser['CONFIG']

# global config variables
testJsonPath     = f"{modulePath}/tests/testJson"
testDataDumpPath = f"{modulePath}/tests/dataDump.log"
testing = False

# logger
import logging
logger = logging.getLogger('degooged_tube')
