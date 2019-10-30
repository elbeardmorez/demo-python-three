import sys
import argparse

verbose = 0


def debug(*args):
    if verbose > 0:
        print("[debug]", *args)


def crawl(target):

    debug(f"crawling '{target}'")


def spider():

    parser = argparse.ArgumentParser(
        description='A spider that crawles')
    parser.add_argument(
        'target', metavar='TARGET', type=str,
        help="base url to initialise crawl from")
    parser.add_argument(
        '-v', '--verbose', action='store_const',
        const=True, default=False,
        help="increase the level of information output")

    if not sys.argv[1:]:
        parser.print_help(sys.stderr)
        print(f"\nmissing args!")
        exit(0)

    args = parser.parse_args()

    target = args.target
    global verbose
    verbose = args.verbose

    crawl(target)


if __name__ == "__main__":
    spider()
