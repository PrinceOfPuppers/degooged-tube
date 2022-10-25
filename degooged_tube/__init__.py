from degooged_tube import config as cfg
from signal import signal,SIGINT,SIGABRT,SIGTERM,Signals, SIG_IGN
import multiprocessing
from multiprocessing.pool import Pool
import sys
from typing import Union


__version__ = "1.0.1"

pool:Union[Pool, None] = None


class _NoInterrupt:
    inNoInterrupt = False
    signalReceived=False

    def __enter__(self):
        if self.signalReceived:
            self.signalReceived = False
            sys.exit()

        self.inNoInterrupt=True


    def __exit__(self, type, value, traceback):
        self.inNoInterrupt=False
        if self.signalReceived:
            self.signalReceived = False
            if pool is not None:
                pool.close()
            sys.exit()

    def handler(self,sig,frame):
        if not self.inNoInterrupt:
            if pool is not None:
                pool.close()
            sys.exit()

        self.signalReceived = True
        cfg.logger.info(f'{Signals(2).name} Received, Closing after this Operation')

    def simulateSigint(self):
        '''can be used to trigger intrrupt from another thread'''
        self.signalReceived = True



noInterrupt = _NoInterrupt()
signal(SIGINT,noInterrupt.handler)

def setupPool():
    signal(SIGINT, SIG_IGN)
    # pool will ignore signal and let parent process close
    global pool
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    signal(SIGINT,noInterrupt.handler)
    return pool

def getPool():
    global pool
    if pool is None:
        return None
    return pool


def main():
    from degooged_tube.cli import cli
    cli()
