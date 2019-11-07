import urllib
from .parser import parse
from .exceptions import FatalException
from .utils import trace, dump_response, cookies_update
import src.api as api
import src.remote as remote


class scraper:
    class __scraper(remote.webclient):
        state = None
        client = None

        def __init__(self, state):
            # super(__scraper, self).__init__()
            remote.webclient.__init__(self)
            self.state = state

        async def scrape(self, url):

            trace(1, f"scraping: '{url}'")

            response = await self.pull(url)
            dump_response(response)

            if response.code == 302:
                location = response.headers['location']
                if location.find(self.state.target) == -1:
                    location = urllib.parse.urljoin(
                        self.state.target.rstrip('/'),
                        location.lstrip('/'))
                if location.find('login') > -1:
                    if not await api.spdr_login(location, self.state):
                        raise FatalException("login failure")
                    api.spdr_security_override(
                        'low', self.request_headers, self.state)
                    response = await self.client.fetch(
                                   url, headers=self.request_headers,
                                   follow_redirects=False, raise_error=False)

                if response.code == 302:
                    return [response.headers['location']]

            return parse(response.body, 'a', 'href')

        def cookies_sync(self, headers):
            cookies_update(headers, self.request_headers)
            trace(2, "updated cookies:")
            trace(2, '\n'.join(headers.get_list('cookie')))

    instance = None

    def __init__(self, state):
        if not scraper.instance:
            scraper.instance = scraper.__scraper(state)

    def __getattr__(self, name):
        return getattr(self.instance, name)
