from bs4 import BeautifulSoup as Soup
from .utils import trace


def parse(body, selector, field=None):
    try:
        dom = Soup(body.decode(), 'lxml')
    except Exception:
        trace(1, "ignoring unparsable content")
        return []
    tokens = dom.select(selector)
    return tokens if not field \
        else [token for token in
              [token.get(field) for token in tokens]
              if token]


def parse_sql_injection_data(body, selector, search):
    # TODO: abstract via lambda arg
    dom = Soup(body.decode(), 'lxml')
    token = dom.select(selector)
    return [p.split(":")[1].strip()
            for p in token[0].children
            if str(p).find(search) > -1]
