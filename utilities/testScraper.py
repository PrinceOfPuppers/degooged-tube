import json
import sys

from degooged_tube.ytApiHacking.jsonScraping.scrapeJsonTree import scrapeJsonTree
import degooged_tube.ytApiHacking.controlPanel as ctrlp

if __name__ == '__main__':
    j = json.load(sys.stdin)
    data = scrapeJsonTree(j, ctrlp.channelInfoScrapeFmt, truncateThreashold=0)
    print(json.dumps(data, indent=2))
