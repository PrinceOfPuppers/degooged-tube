import sys
import json
import logging

import degooged_tube.ytApiHacking.controlPanel as ctrlp
from degooged_tube.ytApiHacking.jsonScraping import scrapeJsonTree,dumpDebugData
import degooged_tube.config as cfg


def setLogging():
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh = logging.FileHandler(cfg.testLogPath)
    fh.setFormatter(formatter)

    cfg.logger.addHandler(fh)
    cfg.logger.setLevel(level=logging.DEBUG)

if __name__ == '__main__':
    setLogging()
    input_str = sys.stdin.read()
    data = json.loads(input_str)

    scraper = ctrlp.uploadScrapeFmt
    debugData = []
    res = scrapeJsonTree(data, scraper, debugDataList=debugData, percentRequiredKeys=1.0)

    dumpDebugData(debugData)

    print(res)
