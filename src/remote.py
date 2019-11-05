import tornado
from tornado import httpclient, httputil
from tornado.web import Application as httpserver, RequestHandler as handler
import src.api as api
from .exceptions import FatalException


class webclient:
    request_headers = None

    def __init__(self):
        httpclient.AsyncHTTPClient.configure(
            "tornado.curl_httpclient.CurlAsyncHTTPClient")
        self.client = httpclient.AsyncHTTPClient(force_instance=True)

        self.request_headers = httputil.HTTPHeaders()
        self.request_headers.add("Keep-Alive", "timeout=5, max=100")
        self.request_headers.add("Connection", "Keep-Alive")
        self.request_headers.add("DNT", "1")
        self.request_headers.add("Upgrade-Insecure-Requests", "1")

    def __del__(self):
        self.client.close()

    async def header(self, url, name):
        try:
            response = await self.client.fetch(
                url, method='HEAD',
                headers=self.request_headers, raise_error=False)
            return response.headers.get_list(name)
        except Exception as e:
            raise FatalException(e)

    async def pull(self, url, follow=False):
        try:
            return await self.client.fetch(
                url, headers=self.request_headers,
                follow_redirects=follow, raise_error=False)
        except Exception as e:
            raise FatalException(e)

    async def push(self, url, body=None, follow=False):
        try:
            return await self.client.fetch(
                url, method='POST', body=body,
                headers=self.request_headers,
                follow_redirects=follow, raise_error=False)
        except Exception as e:
            raise FatalException(e)


class next_url_handler(handler):
    def initialize(self, state):
        self.state = state

    async def get(self):
        next_ = api.spdr_next_url(self.state)
        if next_:
            self.set_status(200)
            self.finish({'url': next_})
        else:
            self.set_status(500)
            self.finish()


class add_links_handler(handler):
    def initialize(self, state):
        self.state = state

    def post(self):
        url = self.decode_argument('url')
        links = self.decode_argument('links')
        api.spdr_add_links(url, links, self.state)
        self.set_status(200)
        self.finish()


class webserver:
    state = None
    server = None
    loop = None

    def __init__(self, state):
        self.state = state
        httpclient.AsyncHTTPClient.configure(
            "tornado.curl_httpclient.CurlAsyncHTTPClient")
        self.client = httpclient.AsyncHTTPClient(force_instance=True)

        self.server = httpserver([
            ('/next_url', next_url_handler, {'state': self.state}),
            ('/add_links', add_links_handler, {'state': self.state})
        ])
        self.server.listen(self.state.service[1])
        loop = tornado.ioloop.IOLoop(make_current=False)
        loop.start()

    def __del__(self):
        self.server.stop()
