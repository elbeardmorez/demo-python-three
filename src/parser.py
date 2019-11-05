from bs4 import BeautifulSoup as Soup


def parse(body, selector, field=None):
    dom = Soup(body.decode(), 'lxml')
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
