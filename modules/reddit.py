import sys
import time
import praw
import threading
from discord import Color
from modules.module import Module, Announcer
from traceback import format_exception, format_exc
from utils import Config

class RedditModule(Module):
    CHANNEL_ID = Config.getModuleSetting('reddit', 'announcements')

    def __init__(self, client):
        Module.__init__(self, client)

        reddit = self.reddit = praw.Reddit(
            client_id=Config.getModuleSetting('reddit', 'clientID'),
            client_secret=Config.getModuleSetting('reddit', 'clientSecret'),
            user_agent=Config.getModuleSetting('reddit', 'ua'),
            username=Config.getModuleSetting('reddit', 'username'),
            password=Config.getModuleSetting('reddit', 'password')
        )

        self.subredditName = Config.getModuleSetting('reddit', 'subreddit')
        self.rTTR = reddit.subreddit(self.subredditName)

        self.postRestarts = 0
        self.commentRestarts = 0

        self.readyToStop = False

        self.postStream = threading.Thread(target=self.streamPosts, name='PostStream-Thread').start()
        self.commentStream = threading.Thread(target=self.streamComments, name='CommentStream-Thread').start()
        self.liveStream = None

        self.live = Config.getModuleSetting('reddit', 'live')
        if self.live:
            NewUpdateAnnouncement.CHANNEL_ID = self.live['announcements']
            if self.live['id']:
                self.liveStream = threading.Thread(target=self.streamLive, name='LiveStream-Thread').start()

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
            if self.postRestarts > 3:
                n = 'The module has encountered a high number of exceptions. It will be disabled until the issue can be resolved.'
                print('{} was disabled for encountering a high number of exceptions.\n\n{}'.format(self.__class__.__name__, format_exc()))
            else:
                n = 'The module will restart momentarily.'
                print('{} was restarted after encountering an exception.\n\n{}'.format(self.__class__.__name__, format_exc()))

            self.pendingAnnouncements.append(
                (
                    Config.getSetting('botspam'), 
                    '**An unprompted exception occured in _{}_.**\n{}\n```\n{}```'.format(self.__class__.__name__, n, format_exc()),
                    {'module': self}
                )
            )

            if self.postRestarts > 3:
                self.readyToStop = True
                return

            if self.RESTART_ON_EXCEPTION:
                self.postRestarts += 1
                time.sleep(5)
                self.postStream = threading.Thread(target=self.streamPosts, name='PostStream-Thread').start()


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
            if self.commentRestarts > 3:
                n = 'The module has encountered a high number of exceptions. It will be disabled until the issue can be resolved.'
                print('{} was disabled for encountering a high number of exceptions.\n\n{}'.format(self.__class__.__name__, format_exc()))
            else:
                n = 'The module will restart momentarily.'
                print('{} was restarted after encountering an exception.\n\n{}'.format(self.__class__.__name__, format_exc()))

            self.pendingAnnouncements.append(
                (
                    Config.getSetting('botspam'), 
                    '**An unprompted exception occured in _{}_.**\n{}\n```\n{}```'.format(self.__class__.__name__, n, format_exc()),
                    {'module': self}
                )
            )

            if self.commentRestarts > 3:
                self.readyToStop = True
                return

            if self.RESTART_ON_EXCEPTION:
                self.commentRestarts += 1
                time.sleep(5)
                self.commentStream = threading.Thread(target=self.streamPosts, name='CommentStream-Thread').start()

    def streamLive(self):
        newUpdate = False
        for update in praw.models.util.stream_generator(self.reddit.live(self.live['id']).updates, pause_after=0):
            if self.client.readyToClose or self.readyToStop:
                break
            elif update is None:
                newUpdate = True
                continue
            elif newUpdate:
                self.announce(NewUpdateAnnouncement, update)

    def stopTracking(self):
        super().stopTracking()
        self.readyToStop = True


class NewPostAnnouncement(Announcer):
    def announce(module, submission):
        if submission.is_self:
            desc = submission.selftext.split('\n')
            if len(desc) > 1:
                desc = desc[0]
                i = -1
                while desc[i] in ['.', '?', '!', ':', ';']:
                    i -= 1
                desc = desc[:(i + 1) or None] + '...'
            else:
                desc = desc[0]
        else:
            desc = 'Links to `{}`. [View the post instead.]({})'.format(submission.domain, "https://www.reddit.com" + submission.permalink)

        flair = submission.author_flair_css_class
        color = Color.default()
        authorIcon = None
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
            thumbnail = None

        embed = module.createDiscordEmbed(title=submission.title, description=desc, url=submission.url, color=color)
        if authorIcon:
            embed.set_author(name=submission.author, icon_url=authorIcon)
        else:
            embed.set_author(name=submission.author)
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)

        embed.set_footer(text='/r/{} - New Post'.format(module.subredditName))
        #embed.add_field(name='Actions', value='')

        return embed

class NewCommentAnnouncement(Announcer):
    def announce(module, comment):
        desc = comment.body.split('\n')
        if len(desc) > 1:
            desc = desc[0]
            i = -1
            while desc[i] in ['.', '?', '!', ':', ';']:
                i -= 1
            desc = desc[:(i + 1) or None] + '...'
        else:
            desc = desc[0]

        color = Color.default()
        authorIcon = None

        flair = comment.author_flair_css_class
        if flair and 'team' in flair:
            color = Color.blue()
            authorIcon = 'https://cdn.discordapp.com/emojis/338117947241529344.png'
        elif flair and 'mod' in flair:
            color = Color.green()
            authorIcon = 'https://cdn.discordapp.com/emojis/338254475674255361.png'

        embed = module.createDiscordEmbed(title='Reply to ' + comment.submission.title, description=desc, url="https://www.reddit.com" + comment.permalink(), color=color)
        if authorIcon:
            embed.set_author(name=comment.author, icon_url=authorIcon)
        else:
            embed.set_author(name=comment.author)

        embed.set_footer(text='/r/{} - New Comment'.format(module.subredditName))
        #embed.add_field(name='Actions', value='')

        return embed

class NewUpdateAnnouncement(Announcer):
    def announce(module, update):
        return update.body

module = RedditModule