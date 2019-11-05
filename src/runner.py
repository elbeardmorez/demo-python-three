import sys
import argparse
import asyncio
from .state import state
import src.api as api


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
            '-v', '--verbose', metavar='LEVEL',
            default=0, type=int,
            help="increase the level of information output")

        if not sys.argv[1:]:
            parser.print_help(sys.stderr)
            print(f"\nmissing args!")
            exit(0)

        args = parser.parse_args()

        self.state_.target = args.target
        self.state_.verbose = args.verbose

    def run(self):
        self.parse_args()

        # setup scope expression
        api.spdr_scope(self.state_)

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
