import sys
import time
import praw
import threading
from discord import Color, Embed
from modules.module import Module, Announcer
from traceback import format_exception, format_exc
from utils import Config, assertType

class RedditModule(Module):
    CHANNEL_ID = Config.getModuleSetting('reddit', 'announcements')

    def __init__(self, client):
        Module.__init__(self, client)

        reddit = self.reddit = praw.Reddit(
            client_id=assertType(Config.getModuleSetting('reddit', 'clientID'), str),
            client_secret=assertType(Config.getModuleSetting('reddit', 'clientSecret'), str),
            user_agent=assertType(Config.getModuleSetting('reddit', 'ua'), str),
            username=assertType(Config.getModuleSetting('reddit', 'username'), str),
            password=assertType(Config.getModuleSetting('reddit', 'password'), str)
        )

        self.subredditName = assertType(Config.getModuleSetting('reddit', 'subreddit'), str)
        self.rTTR = reddit.subreddit(self.subredditName)

        self.postStream = None
        self.commentStream = None
        self.liveStream = None
        self.live = None
        self.readyToStop = False

    def streamPosts(self):
        try:
            newPosts = False
            for submission in self.rTTR.stream.submissions(pause_after=0):
                if self.client.readyToClose or self.readyToStop:
                    break
                elif submission is None:
                    newPosts = True
                    continue
                elif newPosts:
                    self.announce(NewPostAnnouncement, submission)
        except Exception as e:
            self.handleError()

    def streamComments(self):
        try:
            newComments = False
            for comment in self.rTTR.stream.comments(pause_after=0):
                if self.client.readyToClose or self.readyToStop:
                    break
                elif comment is None:
                    newComments = True
                    continue
                elif newComments:
                    self.announce(NewCommentAnnouncement, comment)
        except Exception as e:
            self.handleError()

    def streamLive(self):
        try:
            newUpdate = False
            for update in praw.models.util.stream_generator(self.reddit.live(self.live['id']).updates, pause_after=0):
                if self.client.readyToClose or self.readyToStop:
                    break
                elif update is None:
                    newUpdate = True
                    continue
                elif newUpdate:
                    self.announce(NewUpdateAnnouncement, update)
        except Exception as e:
            self.handleError()

    def startTracking(self):
        super().startTracking()
        self.postStream = threading.Thread(target=self.streamPosts, name='PostStream-Thread').start()
        self.commentStream = threading.Thread(target=self.streamComments, name='CommentStream-Thread').start()

        self.live = Config.getModuleSetting('reddit', 'live')
        if self.live:
            NewUpdateAnnouncement.CHANNEL_ID = self.live['announcements']
            if self.live['id']:
                self.liveStream = threading.Thread(target=self.streamLive, name='LiveStream-Thread').start()

    def stopTracking(self):
        super().stopTracking()
        self.readyToStop = True


class NewPostAnnouncement(Announcer):
    def announce(module, submission):
        if submission.is_self:
            descList = submission.selftext.split('\n')
            if len(descList) > 1:
                desc = descList[0]
                while not desc:
                    descList.pop(0)
                    desc = descList[0]
                i = -1
                while desc[i] in ['.', '?', '!', ':', ';']:
                    i -= 1
                desc = desc[:(i + 1) or None] + '...'
            else:
                desc = descList[0]
        else:
            desc = 'Links to `{}`. [View the post instead.]({})'.format(submission.domain, "https://www.reddit.com" + submission.permalink)

        flair = submission.author_flair_css_class
        color = Color.default()
        authorIcon = Embed.Empty
        if not flair:
            pass
        elif 'team' in flair:
            color = Color.blue()
            authorIcon = 'https://cdn.discordapp.com/emojis/338117947241529344.png'
        elif 'mod' in flair:
            color = Color.green()
            authorIcon = 'https://cdn.discordapp.com/emojis/338254475674255361.png'

        thumbnail = submission.thumbnail
        if 'http' not in thumbnail:
            thumbnail = Embed.Empty

        embed = module.createDiscordEmbed(
            title=submission.author,
            icon=authorIcon,
            subtitle=submission.title,
            info=desc,
            subtitleUrl=submission.url,
            color=color,
            thumbnail=thumbnail,
            footer='/r/{} - New Post'.format(module.subredditName)
        )
        return embed

class NewCommentAnnouncement(Announcer):
    def announce(module, comment):
        descList = comment.body.split('\n')
        if len(descList) > 1:
            desc = descList[0]
            while not desc:
                descList.pop(0)
                desc = descList[0]
            i = -1
            while desc[i] in ['.', '?', '!', ':', ';']:
                i -= 1
            desc = desc[:(i + 1) or None] + '...'
        else:
            desc = descList[0]

        color = Color.default()
        authorIcon = Embed.Empty

        flair = comment.author_flair_css_class
        if flair and 'team' in flair:
            color = Color.blue()
            authorIcon = 'https://cdn.discordapp.com/emojis/338117947241529344.png'
        elif flair and 'mod' in flair:
            color = Color.green()
            authorIcon = 'https://cdn.discordapp.com/emojis/338254475674255361.png'

        embed = module.createDiscordEmbed(
            title=comment.author,
            icon=authorIcon,
            subtitle='Reply to ' + comment.submission.title,
            info=desc,
            subtitleUrl="https://www.reddit.com" + (comment.permalink if type(comment.permalink) == str else comment.permalink()),
            color=color,
            footer='/r/{} - New Comment'.format(module.subredditName)
        )
        return embed

class NewUpdateAnnouncement(Announcer):
    def announce(module, update):
        return update.body

module = RedditModule