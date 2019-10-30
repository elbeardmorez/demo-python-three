import sys
import argparse
import re
import asyncio
from tornado import httpclient, httputil
from bs4 import BeautifulSoup as Soup
import urllib
from collections import OrderedDict

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


def cookies_update(headers_source, headers_target):
    if 'set-cookie' not in headers_source:
        return
    if 'cookie' in headers_target:
        del headers_target['cookie']

    # merge set-cookie pairs
    map_ = OrderedDict()
    for cookies in headers_source.get_list('set-cookie'):
        for cookie in cookies.split(';'):
            if cookie.find("=") == -1:
                cookie += "="
            (k, v) = cookie.strip().split("=")
            map_[k] = v
    headers_target.add("Cookie", "; ".join(f"{k}={v}"
                       if v != '' else k
                       for (k, v) in map_.items()))

    debug("updated cookies:")
    debug('\n'.join(headers_target.get_list('cookie')))


def cookies_override(headers, key, value):
    update = 0
    cookies = []
    if 'cookie' in headers:
        rx = key + '=([a-zA-Z]+)'
        for cookie in headers.get_list('cookie'):
            if cookie.find(f"{key}=") > -1:
                cookies.append(re.sub(rx, f"{key}={value}", cookie))
                update = 1
            else:
                cookies.append(cookie)
        del headers['cookie']
    if update == 0:
        cookies.append(f"{key}={value}")
    for cookie in cookies:
        headers.add("Cookie", cookie)
    debug(f"{'overrode' if update == 0 else 'set'} {key} cookie:")
    debug('\n'.join(headers.get_list('cookie')))


async def crawl(root):

    httpclient.AsyncHTTPClient.configure(
        "tornado.curl_httpclient.CurlAsyncHTTPClient")
    client = httpclient.AsyncHTTPClient(force_instance=True)

    request_headers = httputil.HTTPHeaders()
    request_headers.add("Keep-Alive", "timeout=5, max=100")
    request_headers.add("Connection", "Keep-Alive")
    request_headers.add("DNT", "1")
    request_headers.add("Upgrade-Insecure-Requests", "1")

    # authentication, parse login for credentials
    target = root + '/login.php'
    debug(f"crawling '{target}'")

    response = await client.fetch(target, headers=request_headers)
    dump_response(response, verbose)

    # ensure php session id
    cookies_update(response.headers, request_headers)

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
                   headers=request_headers,
                   body=body, follow_redirects=True)
    dump_response(response, verbose)

    # sql-injection compromise

    # override security cookie
    cookies_override(request_headers, "security", "low")

    target = root + '/vulnerabilities/sqli/'
    debug(f"crawling '{target}'")

    response = await client.fetch(target, headers=request_headers)
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
