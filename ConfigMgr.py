
import ConfigParser


class BotConfig(object):
    """Read IrcBot configuration and answer queries for config keys.
    """

    def __init__(self, file, section):
        self.cfg = ConfigParser.RawConfigParser()
        self.cfg.readfp(file)
        self.main = section

    def get(self, domain, name, optional=False):
        try:
            res = self.cfg.get(domain, name)
        except ConfigParser.NoOptionError:
            if not optional:
                raise
            else:
                res = None
        return res

    def param(self, name):
        return self.cfg.get(self.main, name)

    def channel_list(self, section):
        return [ (item.strip(), self.get(item.strip(), "name")) for item in self.get(self.main, section).split(",") ]

    def channel_name(self, section):
        "note: inconsistent naming of channel section names. fixme!"
        return self.get(section, "name")


