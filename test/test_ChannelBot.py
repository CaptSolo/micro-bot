import os, sys
sys.path.append(os.getcwd()+"/..")

#from TwitSearch import TwitterSearch
from twisted.trial import unittest
import simplejson as json
from StringIO import StringIO

from twisted.words.protocols import irc

from ChannelBot import ChannelBot, ChannelConfigError
from ConfigMgr import BotConfig


class MockFactory(object):

    def __init__(self, cfg):
        self.cfg = cfg
        self.memory = {}


class ChannelBotTest(unittest.TestCase):
    def setUp(self):
        cfg_str = """
[irc-bot]
nick: test-x-bot
server: irc.freenode.net
load: chan1, chan2, chan3

[chan1]
name = #test-bot

[chan2]
name = #test-bot2
tw_url = something
id_url = something_else

[chan3]
name = #test-bot3
tw_url = something
# id_url is missing

[chan4] 
name = some_name
tw_url = something
"""
        self.bot_fact = MockFactory( BotConfig(StringIO(cfg_str), "irc-bot") )
        self.irc = None   # NOTE - may need to use a "real" IRCClient here (later on)

    def test_wrong_name(self):
        self.assertRaises(ChannelConfigError, ChannelBot, self.irc, self.bot_fact, "chan4") 

    def test_no_sources(self):
        self.assertRaises(ChannelConfigError, ChannelBot, self.irc, self.bot_fact, "chan1") 

    def test_all_sources(self):
        c_bot = ChannelBot(self.irc, self.bot_fact, "chan2")
        self.assertTrue(isinstance(c_bot, ChannelBot))

    def test_some_sources(self):
        c_bot = ChannelBot(self.irc, self.bot_fact, "chan3")
        self.assertTrue(isinstance(c_bot, ChannelBot))

    def test_twitter_startup(self):
        def Tmp(a):
            pass

        # Monkey-patch the fn so that it does not launch web requests 
        # ... otherwise deferreds leave the reactor in unclean state after the test
        self.patch(ChannelBot, "getTwitMsgs", Tmp)

        c_bot = ChannelBot(self.irc, self.bot_fact, "chan3")
        c_bot.onJoined("#test-bot3")
        self.assertTrue(c_bot.t_srch is not None)
        c_bot.cleanUp()

    def test_cleanup(self):
        self.todo = "test that ChannelBot cleanup is launched when the bot goes down / offline"
        self.fail("Not implemented")

    def test_identica_startup(self):
        # verify that identica search starts if id_url is defined

        def Tmp(a):
            pass

        # Monkey-patch the fn so that it does not launch web requests 
        # ... otherwise deferreds leave the reactor in unclean state after the test
        self.patch(ChannelBot, "getIdentMsgs", Tmp)
        self.patch(ChannelBot, "getTwitMsgs", Tmp)

        c_bot = ChannelBot(self.irc, self.bot_fact, "chan2")
        c_bot.onJoined("#test-bot2")
        self.assertTrue(c_bot.i_srch is not None)
        c_bot.cleanUp()

    def test_config_failure(self):
# TODO - test situation when one of channels has config errors
#   expected = this ChannelBot does not get created but others do
        self.todo = "when one of channels has config errors, test that ChanBot is not created for it, but that other channels are created ok"
        self.fail("Not implemented")

