from degooged_tube import config as cfg
from signal import signal,SIGINT,SIGABRT,SIGTERM,Signals
import multiprocessing
import sys


__version__ = "0.0.1"

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
            sys.exit()

    def handler(self,sig,frame):
        if not self.inNoInterrupt:
            sys.exit()

        self.signalReceived = True
        cfg.logger.info(f'{Signals(2).name} Received, Closing after this Operation')

    def simulateSigint(self):
        '''can be used to trigger intrrupt from another thread'''
        self.signalReceived = True


noInterrupt = _NoInterrupt()
signal(SIGINT,noInterrupt.handler)

pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())

def main():
    from degooged_tube.cli import cli

    cli()
