import sys
import argparse
import asyncio
from tornado import httpclient

verbose = 0


def debug(*args):
    if verbose > 0:
        print("[debug]", *args)


def dump_response(response):
    print("headers:")
    for (k, v) in response.headers.get_all():
        print(f"{k}: {v}")
    print("cookies:")
    print('\n'.join(response.headers.get_list('set-cookie')))
    print("body:")
    print(response.body.decode())


async def crawl(root):

    httpclient.AsyncHTTPClient.configure(
        "tornado.curl_httpclient.CurlAsyncHTTPClient")
    client = httpclient.AsyncHTTPClient(force_instance=True)

    # authentication
    target = root + '/login.php'
    debug(f"crawling '{target}'")

    response = await client.fetch(target)
    dump_response(response)

    # sql-injection compromise
    target = root + '/vulnerabilities/sqli/'
    debug(f"crawling '{target}'")

    response = await client.fetch(target)
    dump_response(response)

    client.close()


async def spider():

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

    await crawl(target)


if __name__ == "__main__":
    asyncio.run(spider())
