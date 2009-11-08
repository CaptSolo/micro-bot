#!/usr/bin/env python

import sys
import time
import urllib2
from pprint import pprint
from xml.sax.saxutils import unescape

try:
    import json
except ImportError:
    import simplejson as json

class MicroSearch(object):
    """Queries search.twitter.com for query string. Remembers id of last retrieved message,
    and in subsequent calls only returns new messages."""

    def __init__(self, url, channel, print_1st=True, bot_fact=None):
        self.url = url
        self.bot_fact = bot_fact
        self.print_1st = print_1st

        # Key for storing IDs of last msgs retrieved
        self.key = self.url + "|" + channel

    def get_last_id(self):
        return self.bot_fact.memory.get(self.key, 0)
    def set_last_id(self, value):
        self.bot_fact.memory[self.key] = value
    last_id = property(get_last_id, set_last_id)

    def find_last_id(self, data):
        ids = ( int(x['id']) for x in data['results'] )
        return max(ids)

    def read_data(self, msg=None):
        # msg content can be passed in. This is useful when a custom method for retrieving URL content
        #   is preferable. Example: deferred calls in the Twisted framework.
        if msg is None:
            try:
                msg = urllib2.urlopen(self.url).read()
            except urllib2.HTTPError:
                print "got urllib2.HTTPError"
                return

        data = json.loads(msg)
        data['results'].reverse()

        old_last_id = self.last_id
        self.last_id = max(self.find_last_id(data), self.last_id)

        # Don't print anything on the 1st call. Next calls will print only new messages.
        if not self.print_1st and 0 == old_last_id:
            return

        print old_last_id, self.last_id

        for x in data['results']:
            if int(x['id']) > old_last_id:
                # ignore retweets (or we can get too much "spam")
                if not x['text'].startswith("RT @"):
                    yield x

class TwitterSearch(MicroSearch):
    def __init__(self, url, channel, print_1st = True, bot_fact = None):
        super(TwitterSearch,self).__init__(url, channel, print_1st, bot_fact)

    def format_output(self, msg):
        # Twitter does not supply the URL of the entry in its JSON results :(
        msg_url = "http://twitter.com/%s/status/%s" % ( msg['from_user'], msg['id'] )

        msg_date= msg['created_at']
        if msg_date.endswith(" +0000"):
            msg_date = msg_date[0:-len(" +0000")]

        # unescape &quot; in entry text (NOTE: unescape() does not do that by default)
        txt = unescape(msg['text'],{"&quot;": '"'})
        # txt = msg['text'].replace('&quot;', '"')

        tmpl = "Tw [%-12s] %s <<< %s"
        return tmpl % ( msg['from_user'], txt, msg_url )

class IdentiSearch(MicroSearch):
    def __init__(self, url, channel, print_1st = True, bot_fact = None):
        super(IdentiSearch,self).__init__(url, channel, print_1st, bot_fact)

    def format_output(self, msg):
        # IdentiCa does not supply the URL of the entry in its JSON results :(
        msg_url = "http://identi.ca/notice/%s" % (msg['id'],)

        msg_date= msg['created_at']
        if msg_date.endswith(" +0000"):
            msg_date = msg_date[0:-len(" +0000")]

        txt = msg['text']

        tmpl = "Id [%-12s] %s <<< %s"
        return tmpl % ( msg['from_user'], txt, msg_url )

def main():

    #url = "http://search.twitter.com/search.json?q=+SIOC+OR+FOAF+OR+%23deri"

    if len(sys.argv)>1:
        if sys.argv[1]=="twitter":
            url = "http://search.twitter.com/search.json?q=+SIOC+OR+FOAF+OR+%23deri"
            t = TwitterSearch(url)
        elif sys.argv[1]=="identica":
            url = "http://identi.ca/api/search.json?q=SIOC"
            t = IdentiSearch(url)
    else:
        print "Usage: %s [twitter|identica]" % (sys.argv[0],)
        sys.exit(-1)

    n=0
    while 1:
        n+=1
        print "Run #%s" % (n,)

        for i in t.read_data():
            print t.format_output(i)

        time.sleep(60)


if __name__ == "__main__":
    main()
