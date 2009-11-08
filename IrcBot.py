import sys
import time

VERSION_NUM = "1.0"
CONFIG_NAME = "config"

sys.path.append(".")

from twisted.internet import protocol, reactor
from twisted.words.protocols import irc

import ChannelBot

from MicroBlogSearch import TwitterSearch, IdentiSearch

from ConfigMgr import BotConfig

def log(msg):
    print "[%s] %s" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())), msg)


class ChannelNameError(Exception):
    pass


class LogBot(irc.IRCClient):

    version = "micro-bot by @CaptSolo"
    versionNum = VERSION_NUM
    realname = "reports new updates from microblogging sites"
    lineRate = 6

#    def _reallySendLine(self, line):
#        print "[%s] %s" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())), line)
#        irc.IRCClient._reallySendLine(self, line)

    def _get_nickname(self):
        return self.factory.cfg.param("nick")
    nickname = property(_get_nickname)

    def connectionMade(self):
        # connectionMade is called first, before signedOn()

        # Initialize instance variables
        self._channels = {}
        irc.IRCClient.connectionMade(self)
    
    def signedOn(self):
        for sect, chan in self.factory.cfg.channel_list("load"):
            if chan not in self._channels:
                try:
                    self._channels[chan] = ChannelBot.ChannelBot(self, self.factory, sect)
                    self.join(chan)
                except ChannelBot.ChannelConfigError, e:
                    print "config error in section [%s]." % (sect,), self._channels
                    print " >>>", e
                    pass
            else:
                # Trying to join the same channe twice
                raise ChannelNameError("section [%s]: trying to join same channel %s twice." % (sect, chan))

        # IRCClient needs better rate control. still getting "Excess Flood" even w. lineRate=2 sec.
        # self.lineRate = 5 

        # join all channels on the list - XXX
        # (must have got a list of channels)

    def joined(self, channel):
        if channel in self._channels:
# ??? do we need to supply channel at all then ???
            self._channels[channel].onJoined(channel)
        else:
            raise ChannelNameError("joined() a channel that bot was not instructed to join: %s" % (channel, ))


class LogBotFactory(protocol.ClientFactory):
    
    protocol = LogBot
    
    def __init__(self, cfg):
        self.cfg = cfg
        self.memory = {}

    def clientConnectionLost(self, connector, reason):
        print "Lost connection (%s), reconnecting." % (reason,)
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "Could not connect: %s" % (reason,)
        reactor.stop()


if __name__ == '__main__':

    _cfg = BotConfig(open(CONFIG_NAME), "irc-bot")

#    d = shelve.open(filename)

    server = _cfg.param("server")
    port = 6667

    # create factory protocol and application
    f = LogBotFactory(_cfg)

    from twisted.protocols.policies import TrafficLoggingFactory
    f = TrafficLoggingFactory(f, "irc")

    # connect factory to this host and port
    reactor.connectTCP(server, port, f)

    # run bot
    reactor.run()

