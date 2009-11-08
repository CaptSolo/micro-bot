
import os, sys
sys.path.append(os.getcwd()+"/..")

import ConfigParser
from StringIO import StringIO

from twisted.trial import unittest

from ConfigMgr import BotConfig

class ConfigTest(unittest.TestCase):

    def setUp(self):
        # TODO: Add channel keys 
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
        self.cfg = BotConfig(StringIO(cfg_str), "irc-bot")

    def test_get(self):
        self.assertEquals(self.cfg.get("irc-bot", "server"), "irc.freenode.net")
        self.assertEquals(self.cfg.get("irc-bot", "nick"), "test-x-bot")
        self.assertEquals(self.cfg.get("irc-bot", "load"), "chan1, chan2")

    def test_main_param(self):
        self.assertEquals(self.cfg.param("server"), "irc.freenode.net")
        self.assertEquals(self.cfg.param("nick"), "test-x-bot")
        self.assertEquals(self.cfg.param("load"), "chan1, chan2")

    def test_unknown_param(self):
        self.assertRaises(ConfigParser.NoOptionError, self.cfg.param, "unknown")

    def test_channel_list(self):
        channels = self.cfg.channel_list("load")
        self.assertIn(("chan1", "#test-bot"), channels)
        self.assertIn(("chan2", "#test-bot2"), channels)
        self.assertEquals(len(channels), 2)

#    def test_channel_names(self):
#        names = self.cfg.channel_names("load")
#        self.assertIn("#test-bot", names)
#        self.assertIn("#test-bot2", names)
#        self.assertEquals(len(names), 2)

    def test_existing_chaninfo(self):
        chan = "chan1"
        name = self.cfg.get(chan, "name")
        self.assertEquals(name, "#test-bot")

    def test_missing_chaninfo(self):
        chan = "chan_x"
        self.assertRaises(ConfigParser.NoSectionError, self.cfg.get, chan, "name")
