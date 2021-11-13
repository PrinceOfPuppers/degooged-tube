import unittest
import sys
import logging

import argparse

import degooged_tube.tests.unitTests as unitTests
import degooged_tube.tests.integrationTests as integrationTests

import degooged_tube.config as cfg

def parseArgs():
    description = ("unit and integration testing for degooged-tube")

    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('-u','--unit', action='store_true', help='runs all unit tests')
    parser.add_argument('-i','--integration',action='store_true',  help='tests integration using playlist at URL')

    parser.add_argument('-p','--print',action='store_true', help='prints to terminal in addition to tests/testing.log' )

    args,_ = parser.parse_known_args()

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
    cfg.testing = True
    args = parseArgs()

    setLogging(args)

    runall = not (args.unit or args.integration)


    if runall:
        success = unittest.main(unitTests,exit=False, argv=[sys.argv[0]]).result.wasSuccessful()
        if not success:
            sys.exit(1)
        unittest.main(integrationTests,failfast=True, argv=[sys.argv[0]])

    elif args.unit:
        unittest.main(unitTests, failfast=True, argv=[sys.argv[0]])
        
    elif args.integration:
        unittest.main(integrationTests,failfast=True, argv=[sys.argv[0]])

