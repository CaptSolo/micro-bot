import logging

# Configure how we want rdflib logger to log messages
_logger = logging.getLogger("rdflib")
_logger.setLevel(logging.DEBUG)
_hdlr = logging.StreamHandler()
_hdlr.setFormatter(logging.Formatter('%(name)s %(levelname)s: %(message)s'))
_logger.addHandler(_hdlr)


from pprint import pprint

from datetime import datetime
import time
import urllib2

# Sets the search URL to use (when launched as a standalone program)

# XXX identica search RSS is broken, let's use other RSS for now
#SEARCH_URL = "http://identi.ca/search/notice/rss?q=SIOC"
SEARCH_URL = "http://identi.ca/group/foaf/rss"

# select RDF library to use for parsing. allowed values: redland, rdflib 
lib_name = "Redland"

if lib_name.upper()=="REDLAND":
    import RDF

elif lib_name.upper()=="RDFLIB":
    from rdflib.Graph import Graph
    from rdflib import URIRef, Literal, BNode, Namespace, StringInputSource
    from rdflib import RDF

else:
    raise("No library given for parse RDF!")


class QueryRdfLib(object):
    def parseUrl(self, data, url):
# getting errors parsing identi.ca stream w. rdflib (Switching to librdf)
        msg = urllib2.urlopen(url).read()

        g = Graph()

        x = StringInputSource(msg)
        res = g.parse(x)

        for st in res:
            pprint(st)

        return g

    def sparqlMsg(self, g):
        """G = Graph"""

        FOAF = Namespace("http://xmlns.com/foaf/0.1/")
        SIOC = Namespace("http://rdfs.org/sioc/ns#")
        RSS = Namespace("http://purl.org/rss/1.0/")
        ns = dict(foaf=FOAF, sioc=SIOC, rss=RSS)

        q = """
SELECT ?id, ?title, ?nick
WHERE {
    ?id a sioc:MicroblogPost .
    ?id rss:title ?title .
    ?id sioc:has_creator ?creator .
    ?creator foaf:nick ? nick .
} 
"""

        for item in g.query(q, initNs=ns):
            print item

class QueryRedland(object):
    def parseUrl(self, data, url):
# getting errors parsing identi.ca stream w. rdflib (Switching to librdf)
#    msg = urllib2.urlopen(url).read()

        # NOTE: changed signature of parseUrl() in order to supply data to be parsed
        g = RDF.Model()
        parser = RDF.Parser(name="rdfxml")
        parser.parse_string_into_model(g, data, url)

        return g

    def sparqlMsg(self, g):
        """G = Graph"""

        # could optimize by hiding SPARQL requests to a particular RDF lib
        # in: SPARQL queries - out: dictionary of results

        nspaces = { "foaf" : "http://xmlns.com/foaf/0.1/",
            "dc"   : "http://purl.org/dc/elements/1.1/",
            "sioc" : "http://rdfs.org/sioc/ns#",
            "sioct": "http://rdfs.org/sioc/types#",
            "rss"  : "http://purl.org/rss/1.0/" }

        q = ""
        for (a,b) in nspaces.items():
            q += "PREFIX %s: <%s>\n" % (a,b)

        # XXX sioct:MicroBlog post is incorrectly used as a property. TODO: file a ticket at laconi.ca
        q += """
    SELECT ?id, ?title, ?date, ?nick
    WHERE {
        ?x sioct:MicroblogPost ?id .
        ?id rss:title ?title .
        ?id dc:date ?date . 
        ?id sioc:has_creator ?creator .
        ?creator foaf:nick ?nick .
    } 
    """
        
        res = RDF.SPARQLQuery(q).execute(g)

        buf = []
        for item in res:
            # TODO - auto-convert SPARQL fields to assoc. array
            # OR - name SPARQL fields properly and be done w. it
            tmp = {}

            tmp['text'] = str(item['title'])

            # parse W3C datetime format
            tmp_dt = str(item['date'])
            # strptime does not understand time-zone offset (for ver. < 2.6), let's remove it
            if tmp_dt.endswith("+00:00"):
                tmp_dt = tmp_dt[:-len("+00:00")]
            tmp['date'] = datetime.strptime(tmp_dt, "%Y-%m-%dT%H:%M:%S")
            tmp['from_user'] = str(item['nick'])
            tmp['url'] = str(item['id'].uri) # XXX: ambiquous use of "id"
            tmp['id'] = tmp['url'].split("/")[-1]

            # remove "nickname: " from start of messages
            intro = tmp['from_user']+": "
            if tmp['text'].startswith(intro):
                tmp['text'] = tmp['text'][len(intro):]

            buf.append(tmp)

        return buf


class IdenticaSearch:
    """Monitors identi.ca RSS/RDF feeds for updates.
    
The original name comes from monitoring new search results 
but this class can be used to track the regular identi.ca feeds too.
"""

    def __init__(self, url, print_1st=True):
        self.lib = selectLib() 

        self.url = url

        self.last_id = 0
        self.print_1st = print_1st

    def find_last_id(self, data):
        ids = ( int(x['id']) for x in data )
        return max(ids)

    def read_data(self, msg=None):
        # msg content can be passed in. This is useful when a custom method for retrieving URL content
        #   is preferable. Example: deferred calls in the Twisted framework.
        if msg is None:
            try:
                msg = urllib2.urlopen(self.url).read()
            except urllib2.HTTPError:
                print "Error: urllib2.HTTPError at", self.url
                return

        g = self.lib.parseUrl(msg, self.url)    
        data = self.lib.sparqlMsg(g)

        # are result expected to be sorted? the code below is relying on that, but there is no guarantee
        data.reverse()

        old_last_id = self.last_id
        self.last_id = self.find_last_id(data)

        # Don't print anything on the 1st call. Next calls will print only new messages.
        if not self.print_1st and 0 == old_last_id:
            return

        print old_last_id, self.last_id

        # cut off data to 20 most recent entries
        # NOTE: used here to prevent "Excess Flood" in IRC (caused by limits of Twisted IRCClient rate limiting)
        data = data[-20:]

        for x in data:
            if int(x['id']) > old_last_id:
                yield x


def selectLib():
    if lib_name.upper()=="REDLAND":
        lib = QueryRedland()
    elif lib_name.upper()=="RDFLIB":
        lib = QueryRdfLib()
    else:
        raise "No RDF library selected!"

    return lib

def format_output(msg):
    msg_url = msg['url']
    # NOTE: had to add .decode("utf-8") or later calls to encode() were complaining re. illegal ASCII chars
    txt = msg['text'].decode("utf-8") # unescape(msg['text'])

    tmpl = "Id [%-9s] %s <<< %s @ %s"
    return tmpl % ( msg['from_user'], txt, msg['date'], msg_url )

def main():
    # should not print anything because printing of the initial data batch is suppressed

    url = SEARCH_URL

    print "Zero run"
    t1 = IdenticaSearch(url, print_1st=False)

    for i in t1.read_data():
        pprint(format_output(i))

    # start again, this time printing the initial batch as well
    t = IdenticaSearch(url)

    n=0
    while 1:
        n+=1
        print "Run #%s" % (n,)

        for i in t.read_data():
            pprint(format_output(i))

        time.sleep(60)


if __name__ == "__main__":
    main()
