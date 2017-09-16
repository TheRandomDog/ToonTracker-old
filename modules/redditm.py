import praw
import threading
import time
from discord import Color
from modules.module import Module, Announcer
from utils import Config

class TFRedditModule(Module):
    CHANNEL_ID = Config.getModuleSetting('reddit', 'live')['announcements']

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
        self.toonfestStream = threading.Thread(target=self.streamPosts, name='ToonfestStream-Thread').start()

        self.readyToStop = False

    def streamPosts(self):
        time.sleep(10)
        
        newPosts = False
        for submission in self.rTTR.stream.submissions(pause_after=0):
            if self.client.readyToClose or self.readyToStop:
                break
            elif submission is None:
                newPosts = True
                continue
            elif newPosts and 'toonfest' in submission.title.lower():
                self.announce(NewPostAnnouncement, submission)

    def stopTracking(self):
        super().stopTracking()
        self.readyToStop = True


class NewPostAnnouncement(Announcer):
    def announce(module, submission):
        if submission.is_self:
            return submission.url
        else:
            return 'https://www.reddit.com' + submission.permalink

module = TFRedditModule