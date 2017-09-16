from discord import Color, Embed

class ExtServer:
    NAME = 'Toontown Server'
    ICON_URL = None
    DISCORD_COLOR = None
    ALIASES = ()

    def __init__(self):
        self.pendingAnnouncements = []

    def collectData(self):
        pass

    def handleData(self, data):
        pass

    def loopIteration(self):
        pass

    def announce(self, announcer, *args, **kwargs):
        announcement = [announcer]
        announcement.extend(args)
        announcement.append(kwargs)
        self.pendingAnnouncements.append(announcement)

    def createDiscordEmbed(self, title, description=Embed.Empty, *, multipleFields=False, color=None, url=None, **kwargs):
        title = '{} - {}'.format(self.NAME, title)

        if multipleFields:
            embed = Embed(color=color if color else self.DISCORD_COLOR, **kwargs)
            # If we have multiple inline fields, the thumbnail might push them off.
            # Therefore, we'll use the author space to include the icon url.
            embed.set_author(name=title, icon_url=self.ICON_URL if self.ICON_URL else Embed.Empty)
        elif url:
            embed = Embed(title=title, description=description, url=url, color=color if color else self.DISCORD_COLOR, **kwargs)
            if self.ICON_URL:
                embed.set_thumbnail(url=self.ICON_URL)
        else:
            embed = Embed(color=color if color else self.DISCORD_COLOR, **kwargs)
            embed.add_field(name=title, value=description)
            if self.ICON_URL:
                embed.set_thumbnail(url=self.ICON_URL)

        return embed


class ExtRewritten(ExtServer):
    NAME = 'Toontown Rewritten'
    ICON_URL = 'https://b.thumbs.redditmedia.com/CaGOcFYws8iwxH1ZqAt0_NYMsPZrtwCG14oRL0kkX_c.png'
    DISCORD_COLOR = Color.green()
    ALIASES = ('ttr', 'rewritten', 'toontown rewritten')