import sys
import logging
import argparse
import degooged_tube.config as cfg
from degooged_tube import setupPool


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
    fh = logging.FileHandler(cfg.testLogPath)
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
    cfg.testing = True
    setupPool()

    runall = not (args.unit or args.integration)
    import unittest
    loader = unittest.TestLoader()
    runner = unittest.TextTestRunner(failfast= True)

    if runall:
        import degooged_tube.tests.unitTests as unitTests
        suite = loader.loadTestsFromModule(unitTests)
        result = runner.run(suite)

        if result.wasSuccessful():
            import degooged_tube.tests.integrationTests as integrationTests
            suite = loader.loadTestsFromModule(integrationTests)
            runner.run(suite)

    elif args.unit:
        import degooged_tube.tests.unitTests as unitTests
        suite = loader.loadTestsFromModule(unitTests)
        result = runner.run(suite)
        
    elif args.integration:
        import degooged_tube.tests.integrationTests as integrationTests
        suite = loader.loadTestsFromModule(integrationTests)
        runner.run(suite)

