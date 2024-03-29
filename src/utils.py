from collections import OrderedDict
import re
from .state import state


def trace(minimum_verbosity, *args):
    state_ = state()
    type_ = 'info' if minimum_verbosity == 0 \
            else ('debug' if minimum_verbosity > 0 else 'error')
    if state_.verbosity >= minimum_verbosity:
        print(f"[{type_}]", *args)


def dump_response(response):
    state_ = state()
    if state_.verbosity < 5:
        return
    if state_.verbosity >= 5:
        print("headers:")
        for (k, v) in response.headers.get_all():
            print(f"{k}: {v}")
        print("cookies:")
        print('\n'.join(response.headers.get_list('set-cookie')))
    if state_.verbosity >= 6:
        print("body:")
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
    return "updated" if update == 1 else "set"
