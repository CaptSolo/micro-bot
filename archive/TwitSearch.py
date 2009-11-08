
from pprint import pprint
from xml.sax.saxutils import unescape
import sys
import time
import urllib2

try:
    import json
except ImportError:
    import simplejson as json

SEARCH_URL = "http://search.twitter.com/search.json?q=+SIOC+OR+FOAF+OR+%23deri"

class MicroSearch:
    """Queries search.twitter.com for query string. Remembers id of last retrieved message,
    and in subsequent calls only returns new messages."""

    def __init__(self, url, print_1st=True):
        self.url = url

        self.last_id = 0
        self.print_1st = print_1st

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
                yield x

def format_output(msg):
    msg_url = "http://twitter.com/%s/status/%s" % ( msg['from_user'], msg['id'] )
    txt = unescape(msg['text'])
    tmpl = "Tw [%-9s] %s <<< %s"
    return tmpl % ( msg['from_user'], txt, msg_url )

def main():
    # should not print anything because printing of the initial data batch is suppressed

    url = SEARCH_URL

    print "Zero run"
    t1 = TwitterSearch(url, print_1st=False)

    for i in t1.read_data():
        pprint(format_output(i))

    # start again, this time printing the initial batch as well
    t = TwitterSearch(url)

    n=0
    while 1:
        n+=1
        print "Run #%s" % (n,)

        for i in t.read_data():
            pprint(format_output(i))

        time.sleep(60)


if __name__ == "__main__":
    main()
