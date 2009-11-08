import os, sys
sys.path.append(os.getcwd()+"/..")

#from TwitSearch import TwitterSearch
import simplejson as json
from StringIO import StringIO

from twisted.trial import unittest
from twisted.words.protocols import irc

from ConfigMgr import BotConfig

import IrcBot

"""How to test LogBot:

- check that all configs are set
(from the factory or init)

- check that is logins to the list of channels
(have methods "tick" when join is triggered)
(then check afterwards if all channels are ticked)

"""


# XXX Must test that unsuccessful connects and channel joins
#   are reported (or exceptions raised) and that they do NOT
#   FAIL silently!

class ChannelAlreadyJoined(Exception):
    """This exception is raised if trying to join a channel 
    that was already joined.
    """


class MockIrcClient(object):
    def __init__(self):
        self._joined = {}

    def join(self, channel, key=None):
        if self._joined.has_key(channel):
            raise ChannelAlreadyJoined(channel)
        else:
            self._joined[channel] = (True, key)

    def joined(self, channel):
        print "<<< joined() called with:", channel
        pass

    def connectionMade(self):
        pass


class MockFactory(object):

    def __init__(self, cfg):
        self.cfg = cfg

class MockChannelBot(object):
    _run = {}
    def __init__(self, irc, cfg, cfg_domain):
        if not self._run.has_key('init'):
            self._run['init'] = []
        self._run['init'].append(cfg_domain)

#        print "\n\tMochChannelBot.__init__ called with: ", irc, cfg, cfg_domain
#        print "\t>>> ", self._run

    def _cleanUp():
        # Clean up the _run queue between test runs
        MockChannelBot._run = {}
    _cleanUp = staticmethod(_cleanUp)

    def onJoined(self, channel):
        if not self._run.has_key('onJoined'):
            self._run['onJoined'] = []
        self._run['onJoined'].append(channel)

#        print "\tMochChannelBot.onJoined called with: ", channel
#        print "\t>>> ", self._run


class LogBotTest(unittest.TestCase):

    def setUp(self):
        irc.IRCClient = MockIrcClient
        reload(IrcBot)

        self.bot = IrcBot.LogBot()
        cfg_str = """
[irc-bot]
nick: test-x-bot
server: irc.freenode.net
load: chan1, chan2

[chan1]
name = #test-bot

[chan2]
name = #test-bot2
"""
        cfg = BotConfig(StringIO(cfg_str), "irc-bot")
        self.bot.factory = MockFactory(cfg)
       
        self.patch(IrcBot.ChannelBot, "ChannelBot", MockChannelBot)
        # Clear the list of instance methods that were run
        MockChannelBot._cleanUp()

        self.bot.connectionMade()

    def tearDown(self):
        reload(irc)
        reload(IrcBot)

    def test_signon_and_join(self):
        """Check that ChannetBot(s) are created only once and that their number equals the number of channels to load"""
        tmp = IrcBot.ChannelBot.ChannelBot
        self.bot.signedOn()
        self.bot.joined("#test-bot")
        self.assertEquals(len(tmp._run['init']), 2)

    def test_join_on_signon(self):
        self.bot.signedOn()
        self.assertIn("#test-bot", self.bot._joined)
        self.assertIn("#test-bot2", self.bot._joined)
        self.assertEquals(len(self.bot._joined), 2)

    def test_channels_on_signon(self):
        self.assertEquals(len(self.bot._channels), 0)

        self.bot.signedOn()
        self.assertIn("#test-bot", self.bot._channels)
        self.assertIn("#test-bot2", self.bot._channels)
        self.assertEquals(len(self.bot._channels), 2)

        # verify that ChannelBot(s) are created as required
        self.assertTrue(isinstance(self.bot._channels['#test-bot'], IrcBot.ChannelBot.ChannelBot))
        self.assertTrue(isinstance(self.bot._channels['#test-bot2'], IrcBot.ChannelBot.ChannelBot))

    def test_on_joined(self):
        tmp = IrcBot.ChannelBot.ChannelBot

        # check that ChannelBot._run is empty
        self.assertEquals(len(tmp._run), 0)

        self.bot.signedOn()
        self.bot.joined("#test-bot")

        self.assertEquals(len(tmp._run['onJoined']), 1)
        self.assertIn("#test-bot",tmp._run['onJoined'])

        # TODO - what do we want to do when onJoined() ?
        # A: start reporting search matches (optional: report matches 
        #    which were not reported yet (from previous time)

        # signedOn() will initialize all vars and be started 
        # earlier - when IrcBot starts. 
        #   Q: when to start running LoopingCall()?

# XXX - test that multiple joins to the same chan raise errors

    def test_version_info(self):
        """Verify that bot version information is set"""

        self.assertTrue(len(self.bot.version) > 0)
        self.assertTrue(len(self.bot.realname) > 0)
        self.assertEquals(self.bot.versionNum, IrcBot.VERSION_NUM)

    def test_nonexisting_info(self):
        self.assertRaises(AttributeError, lambda: self.bot.some_info)

    def test_nickname(self):
        self.assertEquals(self.bot.nickname, self.bot.factory.cfg.param("nick"))

    def test_wrong_channel(self):
        self.bot.signedOn()
        self.assertRaises(IrcBot.ChannelNameError, self.bot.joined, "#some-channel")

class ChannelConfigErrorTest(unittest.TestCase):
    def setUp(self):
        irc.IRCClient = MockIrcClient
        reload(IrcBot)

        cfg_str = """
[irc-bot]
nick: test-x-bot
server: irc.freenode.net
load: chan1

[chan1]
name = #test-bot
"""
        self.cfg = BotConfig(StringIO(cfg_str), "irc-bot")
        self.bot = IrcBot.LogBot()
        self.bot.factory = MockFactory(self.cfg)
        self.bot.connectionMade()

    def tearDown(self):
        reload(irc)
        reload(IrcBot)

    def test_config(self):
        # Test the path which catches ChannelConfigError and prints the error message
        #  - to check if the code can find the exception being catched (imported from another module)
        self.bot.signedOn()
        pass


from twisted.internet import protocol, reactor

class IrcBotFactoryTest(unittest.TestCase):
    def test_missing_nick(self):
        """Test that bot factory terminates execution if nick is missing from the config."""
        cfg_str = """
[irc-bot]
server: irc.freenode.net
load: chan1, chan2
"""
        self.cfg = BotConfig(StringIO(cfg_str), "irc-bot")
        self.failUnlessRaises(SystemExit, IrcBot.LogBotFactory, self.cfg)

    def test_missing_server(self):
        """Test that bot factory terminates execution if server is missing from the config."""
        cfg_str = """
[irc-bot]
nick: test-bot
load: chan1, chan2
"""
        self.cfg = BotConfig(StringIO(cfg_str), "irc-bot")
        self.failUnlessRaises(SystemExit, IrcBot.LogBotFactory, self.cfg)

    def test_all_ok(self):
        """Test that bot factory is created if both nick and server are present."""

        cfg_str = """
[irc-bot]
nick: test-bot
server: irc.freenode.net
load: chan1, chan2
"""
        self.cfg = BotConfig(StringIO(cfg_str), "irc-bot")
        self.f = IrcBot.LogBotFactory(self.cfg)
        self.failUnlessIsInstance(self.f, IrcBot.LogBotFactory)


class IncorrectConfigTest(unittest.TestCase):
    def setUp(self):
        irc.IRCClient = MockIrcClient
        reload(IrcBot)

        cfg_str = """
[irc-bot]
nick: test-x-bot
server: irc.freenode.net
load: chan1, chan2

[chan1]
name = #test-bot

[chan2]
name = #test-bot
tw_url = something
id_url = something_else
"""
        self.cfg = BotConfig(StringIO(cfg_str), "irc-bot")
        self.bot = IrcBot.LogBot()
        self.bot.factory = MockFactory(self.cfg)

        # Mock the ChannelBot
        self.patch(IrcBot.ChannelBot, "ChannelBot", MockChannelBot)

        MockChannelBot._cleanUp()

        self.bot.connectionMade()

    def tearDown(self):
        reload(irc)
        reload(IrcBot)

    def test_double_join(self):
        """Test that exception is raised if same channel name is loaded
        in multiple config sections.
        """
        self.assertRaises(IrcBot.ChannelNameError, self.bot.signedOn)


class PatchRollbackTest(unittest.TestCase):
    # added for refactoring the test. verify that monkey-patching (previously done
    # at module level) is reversed within other test cases

    def test_rollback(self):
        self.assertFalse(irc.IRCClient == MockIrcClient)
