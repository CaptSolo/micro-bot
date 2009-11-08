import sys
sys.path.append("..")

from MicroBlogSearch import MicroSearch, TwitterSearch
from twisted.trial import unittest
import simplejson as json

class MockFactory(object):

    def __init__(self, cfg = None):
        self.memory = {}
#        self.cfg = cfg

#class MockConfig(object):
#    def get(self, dom, name):
#        if dom == "twitter":
#            if name == "url":
#                return "some url"
#        raise "Unexpected get call"

class SearchFilterTest(unittest.TestCase):
    def setUp(self):
        self.t_srch = TwitterSearch( "http://something.net", "", bot_fact = MockFactory() )

    def test_retweet_filter(self):
        data = { 'results': ( {'id': 12, 'text': 'RT @user something', 'from_user': 'user', 'created_at': 'Sun, Aug 1'}, ) }
        # count the no of records returned
        res = self.t_srch.read_data(json.dumps(data))
        self.assertEqual(len(list(res)), 0)

    def test_border_case(self):
        # retweets (ignored) need to start with "RT @username"
        data = { 'results': ( {'id': 12, 'text': 'RT something', 'from_user': 'user', 'created_at': 'Sun, Aug 1'}, ) }
        # count the no of records returned
        res = self.t_srch.read_data(json.dumps(data))
        self.assertEqual(len(list(res)), 1)

    def test_no_retweet(self):
        data = { 'results': ( {'id': 12, 'text': 'something', 'from_user': 'user', 'created_at': 'Sun, Aug 1'}, ) }
        # count the no of records returned
        res = self.t_srch.read_data(json.dumps(data))
        self.assertEqual(len(list(res)), 1)


class MaxLimitTest(unittest.TestCase):
    def setUp(self):
        self.t_srch = MicroSearch("some url", "", bot_fact = MockFactory())
        self.data = self.gen_test_data(1, 10)

    def gen_test_data(self, start, num):
        data = { 'results' : [] }
        for i in range(start, num+1):
            item = {'id': i, 'text': 'something', 'from_user': 'user', 'created_at': 'Sun, Aug 1'}
            data['results'].append(item)
        return data

    def test_1st_run(self):
        """On the first run, a maximum of <max_tweets> messages should be reported"""
        data = self.gen_test_data(1, 20)
        res = self.t_srch.read_data(json.dumps(data))
        self.assertEqual(len(list(res)), self.t_srch.max_tweets)

    def test_next_run(self):
        """On subsequent runs, all new messages should be reported"""
        # 1st run
        data = self.gen_test_data(1, 20)
        res = self.t_srch.read_data(json.dumps(data))
        # generator from 1st call needs to consumed before next call can be issued
        out = list(res)

        # 2nd run
        data = self.gen_test_data(30, 40)
        res = self.t_srch.read_data(json.dumps(data))
        out = list(res)
        self.assertEqual(len(out), len(data['results']))


class TwitIrregularityTest(unittest.TestCase):
    # Test that if Twitter omits previosly reported tweet, it does not get 
    # sent to IRC channel twice

    def setUp(self):
        self.t_srch = MicroSearch("some url", "", bot_fact = MockFactory())

    def _supply(self, items):
        buf = {}
        buf['results'] = [ {'id': str(o), 'text': 'some-text'} for o in items ]
        # print "\n\t>>>", buf
        data = json.dumps(buf)
        out = list(self.t_srch.read_data(data))
        return out

    def test_last_id_update(self):
#        buf = self._supply([[100,99]])
#        buf = { 'results': [ { 'id': 100 }, { 'id': 99 } ] }
        self._supply([100,99])
        self.assertEquals(self.t_srch.last_id, 100)

    def test_wrong_order(self):
        # test that if newer data is sent, then disappear, that reappear ...
        len_1 = len(self._supply([20]))
        self.assertEquals(self.t_srch.last_id,20)
        self.assertEquals(len_1, 1)

        len_1 = len(self._supply([10]))
        self.assertEquals(self.t_srch.last_id,20)
        self.assertEquals(len_1, 0)

        len_1 = len(self._supply([20]))
        self.assertEquals(self.t_srch.last_id,20)
        self.assertEquals(len_1, 0)

