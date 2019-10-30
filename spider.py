import sys
import argparse
import asyncio
from tornado import httpclient
from bs4 import BeautifulSoup as Soup
import urllib

verbose = 0


def debug(*args):
    if verbose > 0:
        print("[debug]", *args)


def dump_response(response, level=1):
    if level == 0:
        return
    if level >= 1:
        print("headers:")
        for (k, v) in response.headers.get_all():
            print(f"{k}: {v}")
        debug("cookies:")
        print('\n'.join(response.headers.get_list('set-cookie')))
    if level >= 2:
        debug("body:")
        print(response.body.decode())


async def crawl(root):

    httpclient.AsyncHTTPClient.configure(
        "tornado.curl_httpclient.CurlAsyncHTTPClient")
    client = httpclient.AsyncHTTPClient(force_instance=True)

    # authentication, parse login for credentials
    target = root + '/login.php'
    debug(f"crawling '{target}'")

    response = await client.fetch(target)
    dump_response(response, verbose)

    dom = Soup(response.body.decode(), 'lxml')
    token = dom.select_one("form input[name='user_token']").get('value')
    post_data = {
        'Login': 'Login',
        'user_token': token,
        'username': 'admin',
        'password': 'password',
    }
    body = urllib.parse.urlencode(post_data)

    response = await client.fetch(
                   target, method='POST',
                   body=body, follow_redirects=True)
    dump_response(response, verbose)

    # sql-injection compromise
    target = root + '/vulnerabilities/sqli/'
    debug(f"crawling '{target}'")

    response = await client.fetch(target)
    dump_response(response, verbose)

    client.close()


async def spider():

    parser = argparse.ArgumentParser(
        description='A spider that crawles')
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

    target = args.target
    global verbose
    verbose = args.verbose

    await crawl(target)


if __name__ == "__main__":
    asyncio.run(spider())
