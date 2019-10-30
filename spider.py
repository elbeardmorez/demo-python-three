import argparse

verbose = 0


def debug(*args):
    if verbose > 0:
        print("[debug]", *args)


def crawl():

    debug("crawling..")


def spider():

    parser = argparse.ArgumentParser(
        description='A spider that crawles')
    parser.add_argument(
        '-v', '--verbose', action='store_const',
        const=True, default=False,
        help="increase the level of information output")

    args = parser.parse_args()

    global verbose
    verbose = args.verbose

    crawl()


if __name__ == "__main__":
    spider()
