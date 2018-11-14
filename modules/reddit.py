import sys
import time
import praw
import asyncio
import threading
from discord import Color, Embed
from modules.module import Module, Announcer
from traceback import format_exception, format_exc
from utils import Config, assert_type

# Thanks Zac
# https://blogs.gentoo.org/zmedico/2016/09/17/adapting-regular-iterators-to-asynchronous-iterators-in-python/
class AsyncIteratorExecutor:
    """
    Converts a regular iterator into an asynchronous
    iterator, by executing the iterator in a thread.
    """
    def __init__(self, iterator):
        self.__iterator = iterator
        self.__loop = asyncio.get_event_loop()

    def __aiter__(self):
        return self

    async def __anext__(self):
        value = await self.__loop.run_in_executor(None, next, self.__iterator, self)
        if value is self:
            raise StopAsyncIteration
        return value

class RedditModule(Module):
    def __init__(self, client):
        Module.__init__(self, client)

        reddit = self.reddit = praw.Reddit(
            client_id=assert_type(Config.get_module_setting('reddit', 'client_id'), str),
            client_secret=assert_type(Config.get_module_setting('reddit', 'client_secret'), str),
            user_agent=assert_type(Config.get_module_setting('reddit', 'ua'), str),
            username=assert_type(Config.get_module_setting('reddit', 'username'), str),
            password=assert_type(Config.get_module_setting('reddit', 'password'), str)
        )

        self.subreddit_name = assert_type(Config.get_module_setting('reddit', 'subreddit'), str)
        self.subreddit = reddit.subreddit(self.subreddit_name)

        self.post_stream = None
        self.comment_stream = None
        self.live_stream = None
        self.live = None
        self.ready_to_stop = False

        self.post_announcer, self.comment_announcer, self.live_announcer = self.create_announcers(NewPostAnnouncer, NewCommentAnnouncer, NewUpdateAnnouncer)

    async def stream_posts(self):
        try:
            new_posts = False
            async for submission in AsyncIteratorExecutor(self.subreddit.stream.submissions(pause_after=0)):
                if self.client.ready_to_close or self.ready_to_stop:
                    break
                elif submission is None:
                    new_posts = True
                    continue
                elif new_posts:
                    await self.post_announcer.announce(submission)
        except Exception as e:
            await self.handle_error()

    async def stream_comments(self):
        try:
            new_comments = False
            async for comment in AsyncIteratorExecutor(self.subreddit.stream.comments(pause_after=0)):
                if self.client.ready_to_close or self.ready_to_stop:
                    break
                elif comment is None:
                    new_comments = True
                    continue
                elif new_comments:
                    await self.comment_announcer.announce(comment)
        except Exception as e:
            await self.handle_error()

    async def stream_live(self):
        try:
            new_update = False
            async for update in AsyncIteratorExecutor(praw.models.util.stream_generator(self.reddit.live(self.live['id']).updates, pause_after=0)):
                if self.client.ready_to_close or self.ready_to_stop:
                    break
                elif update is None:
                    new_update = True
                    continue
                elif new_update:
                    await self.live_announcer.announce(update)
        except Exception as e:
            await self.handle_error()

    def start_tracking(self):
        super().start_tracking()
        self.post_stream = self.client.loop.create_task(self.stream_posts())
        self.comment_stream = self.client.loop.create_task(self.stream_comments())

        self.live = Config.get_module_setting('reddit', 'live')
        if self.live:
            self.live_announcer.CHANNEL_ID = self.live['announcements']
            if self.live['id']:
                self.live_stream = self.client.loop.create_task(self.stream_live())

    def stop_tracking(self):
        super().stop_tracking()
        self.ready_to_stop = True


class NewPostAnnouncer(Announcer):
    CHANNEL_ID = Config.get_module_setting('reddit', 'announcements')

    async def announce(self, submission):
        if submission.is_self:
            desc_list = submission.selftext.split('\n')
            if len(desc_list) > 1:
                desc = desc_list[0]
                while not desc:
                    desc_list.pop(0)
                    desc = desc_list[0]
                i = -1
                while desc[i] in ['.', '?', '!', ':', ';']:
                    i -= 1
                desc = desc[:(i + 1) or None] + '...'
            else:
                desc = desc_list[0]
        else:
            desc = 'Links to `{}`. [View the post instead.]({})'.format(submission.domain, "https://www.reddit.com" + submission.permalink)

        if len(desc) > 2048:
            last_valid_word_index = desc[:2048].rfind(' ')
            if last_valid_word_index == -1:
                last_valid_word_index = 2045
            desc = desc[:last_valid_word_index] + '...'

        flair = submission.author_flair_css_class
        color = Color.default()
        author_icon = Embed.Empty
        if not flair:
            pass
        elif 'team' in flair:
            color = Color.blue()
            author_icon = 'https://cdn.discordapp.com/emojis/338117947241529344.png'
        elif 'mod' in flair:
            color = Color.green()
            author_icon = 'https://cdn.discordapp.com/emojis/338254475674255361.png'

        thumbnail = submission.thumbnail
        if 'http' not in thumbnail:
            thumbnail = Embed.Empty

        embed = self.module.create_discord_embed(
            title=submission.author,
            icon=author_icon,
            subtitle=submission.title,
            info=desc,
            subtitle_url=submission.url,
            color=color,
            thumbnail=thumbnail,
            footer='/r/{} - New Post'.format(self.module.subreddit_name)
        )
        return await self.send(embed)

class NewCommentAnnouncer(Announcer):
    CHANNEL_ID = Config.get_module_setting('reddit', 'announcements')

    async def announce(self, comment):
        desc_list = comment.body.split('\n')
        if len(desc_list) > 1:
            desc = desc_list[0]
            while not desc:
                desc_list.pop(0)
                desc = desc_list[0]
            i = -1
            while desc[i] in ['.', '?', '!', ':', ';']:
                i -= 1
            desc = desc[:(i + 1) or None] + '...'
        else:
            desc = desc_list[0]

        if len(desc) > 2048:
            last_valid_word_index = desc[:2048].rfind(' ')
            if last_valid_word_index == -1:
                last_valid_word_index = 2045
            desc = desc[:last_valid_word_index] + '...'

        color = Color.default()
        author_icon = Embed.Empty

        flair = comment.author_flair_css_class
        if flair and 'team' in flair:
            color = Color.blue()
            author_icon = 'https://cdn.discordapp.com/emojis/338117947241529344.png'
        elif flair and 'mod' in flair:
            color = Color.green()
            author_icon = 'https://cdn.discordapp.com/emojis/338254475674255361.png'

        embed = self.module.create_discord_embed(
            title=comment.author,
            icon=author_icon,
            subtitle='Reply to ' + comment.submission.title,
            info=desc,
            subtitle_url="https://www.reddit.com" + (comment.permalink if type(comment.permalink) == str else comment.permalink()),
            color=color,
            footer='/r/{} - New Comment'.format(self.module.subreddit_name)
        )
        return await self.send(embed)

class NewUpdateAnnouncer(Announcer):
    CHANNEL_ID = Config.get_module_setting('reddit', 'announcements')

    async def announce(self, update):
        return await self.send(update.body)

module = RedditModule