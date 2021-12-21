import sys
import logging
import degooged_tube.config as cfg
import degooged_tube.ytApiHacking as ytapih
import argparse

def setupLogger():
    stream = logging.StreamHandler(sys.stdout)
    cfg.logger.setLevel(logging.ERROR)
    stream.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    cfg.logger.addHandler(stream)

def parseArgs():
    description = ("gets youtube inital data from the provided url")
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('URL',nargs='?', type=str, help='the url of the page to get')

    args = parser.parse_args()

    return args


if __name__ == '__main__':
    from degooged_tube.ytApiHacking import YtInitalPage
    import json
    setupLogger()
    args = parseArgs()
    page = YtInitalPage.fromUrl(args.URL)

    print(json.dumps(page.initalData, indent = 2))
    #print(json.dumps(page.scrapeInitalData(ytapih.ctrlp.videoInfoScrapeFmt), indent = 2))

