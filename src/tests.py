import unittest
import re

import src.api as api
from state import state


class tiesto(unittest.TestCase):

    state_ = None

    def setUp(self):
        self.state_ = state()
        self.state_.target = 'localhost'

    def test_api_scope(self):
        for (target, test, res) in [
                    ('localhost', 'http://localhost/xyz', 'http://localhost'),
                    ('localhost', 'https://localhost/xyz',
                     'https://localhost'),
                    ('http://localhost/', 'http://localhost',
                     'http://localhost'),
                    ('https://localhost:8080/zyx', 'https://localhost', None),
                    ('localhost', 'ws://localhost/xyz', None),
                ]:
            with self.subTest((target, test, res)):
                self.state_.target = target
                api.spdr_scope(self.state_)
                scoped_url = re.search(self.state_.scope, test)
                if scoped_url:
                    self.assertEqual(scoped_url[0], res)
                else:
                    self.assertEqual(scoped_url, res)


if __name__ == '__main__':
    unittest.main(verbosity=2)
