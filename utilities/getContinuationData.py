import sys
import logging
import degooged_tube.config as cfg
import argparse
from degooged_tube.ytApiHacking.jsonScraping import scrapeJsonTree
import degooged_tube.ytApiHacking.controlPanel as ctrlp

#modified version of help formatter which only prints args once in help message
class ArgsOnce(argparse.HelpFormatter):
    def __init__(self,prog):
        super().__init__(prog,max_help_position=40)

    def _format_action_invocation(self, action):
        if not action.option_strings:
            metavar, = self._metavar_formatter(action, action.dest)(1)
            return metavar
        else:
            parts = []

            if action.nargs == 0:
                parts.extend(action.option_strings)

            else:
                default = action.dest.upper()
                args_string = self._format_args(action, default)
                for option_string in action.option_strings:
                    parts.append('%s' % option_string)
                parts[-1] += ' %s'%args_string
            return ', '.join(parts)

def setupLogger():
    stream = logging.StreamHandler(sys.stdout)
    cfg.logger.setLevel(logging.ERROR)
    stream.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    cfg.logger.addHandler(stream)

def parseArgs():
    description = ("gets youtube data from continuation chain provided \nexample API_URLS: /youtubei/v1/browse /youtubei/v1/next")
    parser = argparse.ArgumentParser(description=description, formatter_class = ArgsOnce)
    parser.add_argument('-i', '--inital-data',action='store_true', help='get inital data')
    parser.add_argument('-n', '--num-data', nargs=1, type=int, default=1, help='number of continuations to do plus inital data if flipped')
    parser.add_argument('INITAL_PAGE_URL',nargs='?', type=str, help='the url that all the continuation tokens start on')
    parser.add_argument('API_URL',nargs='?', type=str, help='the url that is used with the continuation tokens')
    parser.set_defaults(func = lambda args: handler(args, parser))

    args = parser.parse_args()
    return args

def handler(args, parser):
    from degooged_tube.ytApiHacking import YtInitalPage
    from degooged_tube.ytApiHacking.ytContIter import YtContIter
    import json

    if args.INITAL_PAGE_URL is None or args.API_URL is None:
        parser.print_help()
        print('Both INITAL_PAGE_URL and API_URL Required!\n')
        return

    page = YtInitalPage.fromUrl(args.INITAL_PAGE_URL)
    iter = YtContIter(page, args.API_URL, args.inital_data)

    num = args.num_data[0]

    for i in range(num):
        d = iter.getNextRaw()
        if d is None:
            raise Exception("Error Getting Data")
        print(f"================ Iteration {i}/{num} ================\n")
        for i,data in enumerate(d):
            print(f">>> Continuation Chain {i}/{len(d)} Iteration {i}/{num}")
            print(json.dumps(data, indent=2))
            #print((json.dumps(scrapeJsonTree(data, ctrlp.relatedVideosScrapeFmt, percentRequiredKeys=0), indent=2)))
        print("\n=====================================================\n")

if __name__ == '__main__':
    setupLogger()
    args = parseArgs()
    args.func(args)
