import unittest
import logging

import argparse

import degooged_tube.tests.unitTests as unitTests

import degooged_tube.config as cfg

def parseArgs():
    description = ("unit and integration testing for degooged-tube")

    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('-u','--unit', action='store_true', help='runs all unit tests')

    parser.add_argument('-p','--print',action='store_true', help='prints to terminal in addition to tests/testing.log' )

    args,other = parser.parse_known_args()

    return args


def setLogging(args):
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh = logging.FileHandler(f"{cfg.modulePath}/tests/testing.log")
    fh.setFormatter(formatter)

    cfg.logger.addHandler(fh)

    if args.print:
        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        cfg.logger.addHandler(sh)

    cfg.logger.setLevel(level=logging.DEBUG)



if __name__ == "__main__":
    args = parseArgs()

    setLogging(args)

    runall = not args.unit

    if args.unit or runall:
        unittest.main(unitTests)
