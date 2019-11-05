from tornado import httpclient, httputil
from .parser import parse
import src.utils as utils
import src.api as api


class scraper:
    class __scraper():
        state = None
        client = None
        request_headers = None

        def __init__(self, state):
            self.state = state
            httpclient.AsyncHTTPClient.configure(
                "tornado.curl_httpclient.CurlAsyncHTTPClient")
            self.client = httpclient.AsyncHTTPClient(force_instance=True)

            self.request_headers = httputil.HTTPHeaders()
            self.request_headers.add("Keep-Alive", "timeout=5, max=100")
            self.request_headers.add("Connection", "Keep-Alive")
            self.request_headers.add("DNT", "1")
            self.request_headers.add("Upgrade-Insecure-Requests", "1")

        async def scrape(self, url):

            utils.trace(self.state.verbosity, f"scraping: '{url}'")

            response = await self.client.fetch(
                          url, headers=self.request_headers,
                          follow_redirects=False, raise_error=False)
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
