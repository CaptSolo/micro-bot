import os, sys
sys.path.append(os.getcwd()+"/..")

#from TwitSearch import TwitterSearch
from twisted.trial import unittest
import simplejson as json

from StringIO import StringIO

from twisted.words.protocols import irc

"Test that reloading of module works"

class MockIrcClient(object):
    my_name = "MockIrcClient"
    def __init__(self):
        self._joined = {}

    def join(self, channel, key=None):
        if self._joined.has_key(channel):
            raise ChannelAlreadyJoined(channel)
        else:
            self._joined[channel] = (True, key)

    def joined(self, channel):
        pass

class MockIrcClient2(MockIrcClient):
    my_name = "#2 of MockIrcClient"

class MockFactory(object):

    def __init__(self):
        self.cfg_str = """
[irc-bot]
nick: test-x-bot
server: irc.freenode.net
load: chan1, chan2

[chan1]
name = #test-bot

[chan2]
name = #test-bot2
"""
        self.cfg = None

"""
Verify that module get reloaded and, consequently, that the monkey-patching in
setUp() enters into effect even if the module has been imported before
"""

# XXX These tests do not cleanly show down - IrcBot remains redefined and impacts other tests
#  could not figure right away how to properly clean up after it
#  moved to ./archive instead

class LogBotTest(unittest.TestCase):

    def setUp(self):
        self._ic = irc.IRCClient
        irc.IRCClient = MockIrcClient
        import IrcBot
        reload(IrcBot)
        self.bot = IrcBot.LogBot()
        self.bot.factory = MockFactory()
        self.bot.factory.cfg = IrcBot.IrcBotConfig(StringIO(self.bot.factory.cfg_str), "irc-bot")

    def cleanUp(self):
        self.bot.
        irc.IRCClient = self._ic
        import IrcBot
        reload(IrcBot)
        
    def test_join_on_signon(self):
        self.assertEquals(self.bot.my_name, MockIrcClient.my_name)


class LogBotTest2(unittest.TestCase):

    def setUp(self):
        self._ic = irc.IRCClient
        irc.IRCClient = MockIrcClient2
        import IrcBot
        reload(IrcBot)
        self.bot = IrcBot.LogBot()
        self.bot.factory = MockFactory()
        self.bot.factory.cfg = IrcBot.IrcBotConfig(StringIO(self.bot.factory.cfg_str), "irc-bot")

    def cleanUp(self):
        irc.IRCClient = self._ic
        import IrcBot
        reload(IrcBot)
        
    def test_join_on_signon(self):
        self.assertEquals(self.bot.my_name, MockIrcClient2.my_name)
