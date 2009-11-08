
# needed for log messages
# TODO:
#  - separate logging into a module of its own
import time

from twisted.internet import task
from twisted.web.client import getPage

from MicroBlogSearch import TwitterSearch, IdentiSearch

POLL_INTERVAL = 180.0

class ChannelConfigError(Exception):
    pass

class ChannelBot(object):
    def __init__(self, irc, bot_fact, chan_cfg):
        # could also set self.irc when creating channels in the IRCClient
        self.irc = irc
        self.bot_fact = bot_fact

        cfg = bot_fact.cfg

        self.channel = cfg.channel_name(chan_cfg)
        if self.channel[0] != "#":
            raise ChannelConfigError("Channel name must start with #. Error in section[%s], channel name = %s" % (chan_cfg, self.channel))

        self.id_url = cfg.get(chan_cfg, "id_url", optional=True)
        self.tw_url = cfg.get(chan_cfg, "tw_url", optional=True)

        if self.id_url is None and self.tw_url is None:
            raise ChannelConfigError("At least one URL to monitor must be specified in ChannelBot config. Section: [%s]" % (chan_cfg,))

    def send(self, channel, msg):
        # to use channel notices instead of messages, change "irc.msg" to "irc.notice"
        self.irc.msg(channel, msg)

    def onJoined(self, channel):
        if self.channel == channel:
            # XXX launch twit/ident listeners here
            print "[%s] joined %s" % (time.asctime(time.localtime(time.time())),channel)
# XXX !!!
            if self.tw_url:
                self.t_srch = TwitterSearch(self.tw_url, print_1st=True, bot_fact=self.bot_fact )
                self.t_task = task.LoopingCall(self.getTwitMsgs)
                self.t_task.start(POLL_INTERVAL)
            if self.id_url:
                self.i_srch = IdentiSearch(self.id_url, print_1st=True, bot_fact=self.bot_fact )
                self.i_task = task.LoopingCall(self.getIdentMsgs)
                self.i_task.start(POLL_INTERVAL)
        else:
            print "[%s] ERROR - ChannelBot joined channel which it did not have to - %s" % (time.asctime(time.localtime(time.time())),channel)

    def cleanUp(self):
        if hasattr(self,"t_task") and self.t_task:
            self.t_task.stop()
            self.t_task = None

        if hasattr(self,"i_task") and self.i_task:
            self.i_task.stop()
            self.i_task = None

    def getTwitMsgs(self): 
        print "[%s] checking for Twitter messages" % (time.asctime(time.localtime(time.time())),) 
        _url = self.t_srch.url
        getPage(_url).addCallbacks(self.printTwitMsgs)

    def printTwitMsgs(self, msg):
        print "[%s] processing Twitter messages" % (time.asctime(time.localtime(time.time())),) 
        cnt = 0
        for i in self.t_srch.read_data(msg):
            print self.t_srch.format_output(i).encode('utf-8')
            self.send(self.channel, self.t_srch.format_output(i).encode('utf-8'))
            cnt += 1
        print "[%s]   %s new Twitter messages processed" % (time.asctime(time.localtime(time.time())), cnt) 
    
    def getIdentMsgs(self): 
        print "[%s] checking for Identica messages" % (time.asctime(time.localtime(time.time())),) 
        _url = self.i_srch.url
        # XXX add errback callbacks !!!
        getPage(_url).addCallbacks(self.printIdentMsgs)

    def printIdentMsgs(self, msg): 
        print "[%s] processing Identica messages" % (time.asctime(time.localtime(time.time())),) 
        cnt = 0
        for i in self.i_srch.read_data(msg):
            print self.i_srch.format_output(i).encode('utf-8')
            self.send(self.channel, self.i_srch.format_output(i).encode('utf-8'))
            cnt += 1
        print "[%s]   %s new Identica messages processed" % (time.asctime(time.localtime(time.time())), cnt) 


# ChannelBotFactory
    # read config and initiate clients that respond to IRC events
    # do we need special factory at all?

