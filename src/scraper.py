from .parser import parse
import src.utils as utils
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

            utils.trace(self.state.verbosity, f"scraping: '{url}'")

            response = await self.pull(url)
            utils.dump_response(self.state.verbosity, response)

            if response.code == 302:
                location = response.headers['location']
                if location.find(self.state.target) == -1:
                    location = '/'.join([self.state.target.rstrip('/'),
                                         location.lstrip('/')])
                if location.find('login') > -1:
                    if not await api.spdr_login(location, self.state):
                        raise Exception("login failure")
                    api.spdr_security_override(
                        'low', self.request_headers, self.state)
                    response = await self.client.fetch(
                                   url, headers=self.request_headers,
                                   follow_redirects=False, raise_error=False)

                if response.code == 302:
                    return [response.headers['location']]

            return parse(response.body, 'a', 'href')

        def cookies_sync(self, headers):
            utils.cookies_update(headers, self.request_headers)
            utils.trace(self.state.verbosity, "updated cookies:")
            utils.trace(self.state.verbosity,
                        '\n'.join(headers.get_list('cookie')))

    instance = None

    def __init__(self, state):
        if not scraper.instance:
            scraper.instance = scraper.__scraper(state)

    def __getattr__(self, name):
        return getattr(self.instance, name)
