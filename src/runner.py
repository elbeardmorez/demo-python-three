import sys
import argparse
import asyncio
import threading
from .state import state
from .utils import trace
import src.api as api
import src.remote as remote


class runner():

    state_ = None

    def __init__(self):
        self.state_ = state()

    # parse args
    def parse_args(self):

        description = [
          "Given a target host's root, 'spider' searches for basic sql "
          "injection vulnerabilities and returns the database user and "
          "version where successful"
        ]
        parser = argparse.ArgumentParser(
            description=''.join(description))
        parser.add_argument(
            'target', metavar='TARGET', type=str,
            help="base url to initialise crawl from")
        # bug: failure of optional followed by positional
        # https://bugs.python.org/issue9338
        parser.add_argument(
            '-s', '--slave', metavar='HOST:PORT', type=str,
            help="instance slave mode, connecting to master at HOST:POST")
        parser.add_argument(
            '-v', '--verbosity', metavar='LEVEL',
            default=0, type=int,
            help="increase the level of information output")

        if not sys.argv[1:]:
            parser.print_help(sys.stderr)
            trace(-1, f"\nmissing args!")
            exit(0)

        args = parser.parse_args()

        self.state_.target = args.target
        self.state_.verbosity = args.verbosity

        if args.slave:
            self.state_.mode = "slave"
            self.state_.service = (*args.slave.split(':'),)

    def run(self):
        self.parse_args()

        # setup scope expression
        api.spdr_scope(self.state_)

        if self.state_.mode == "master":
            # start tornado web server
            threading.Thread(target=(lambda _: remote.webserver(self.state_)))

            # add a seed url
            self.state_.url_pools['unprocessed'].appendleft(self.state_.target)

        # run event loop
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(api.spdr_process_urls(self.state_))
        finally:
            if not loop.is_closed():
                loop.close()

        return self.state_.url_pools['vulnerable']
