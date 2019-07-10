import discord
import asyncio
import youtube_dl
import sys
import time
import os.path
from utils import get_time_from_seconds

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': os.path.join('extra', 'music', '%(extractor)s-%(id)s-%(title)s.%(ext)s'),
    'restrictfilenames': True,
    'yesplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'before_options': '-nostdin',
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    AGE_RESTRICTED = 'age_restricted'

    def __init__(self, source, *, data, volume=0.5):
        self.error = data.get('error', None)
        if self.error:
            return

        super().__init__(source, volume)

        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.original_duration = data.get('duration')
        self.duration = data.get('modified_duration', self.original_duration)
        self.age_restricted = data.get('age_limit', 0) > 0

    @staticmethod
    def getSpecificFormattedDuration(duration):
        return '{}:{:0>2}'.format(int(duration / 60), int(duration % 60))

    def getFormattedDuration(self):
        return self.getSpecificFormattedDuration(self.duration)

    @classmethod
    async def from_url(cls, url):
        loop = asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        except youtube_dl.utils.DownloadError as e:
            return [cls(None, data={'error': str(e)})]

        sources = []
        entries = data.get('entries', [data])

        for data in entries:
            if not data.get('is_live', False):
                filename = ytdl.prepare_filename(data)
                if not os.path.isfile(filename):
                    await loop.run_in_executor(None, lambda: ytdl.download([data['webpage_url']]))
            else:
                filename = data['url']

            print(data.get('title', None), data.get('duration', None))
            sources.append(cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data))

        return sources

    @classmethod
    def from_timestamp(cls, source, time):
        filename = ytdl.prepare_filename(source.data)
        options = ffmpeg_options.copy()
        options['before_options'] = '-nostdin -ss {}'.format(time)

        if not time.isdigit():
            time = time.split(':')
            seconds = int(time[-1])
            if len(time) > 1:
                seconds += int(time[-2]) * 60
            if len(time) > 2:
                seconds += int(time[-3]) * 3600
        else:
            seconds = int(time)
        source.data['modified_duration'] = source.data['duration'] - seconds

        return cls(discord.FFmpegPCMAudio(filename, **options), data=source.data)

class TuneTracker(discord.Client):
    def __init__(self):
        super().__init__()

        if sys.platform == 'windows':
            discord.opus.load_opus('libopus-x64')

        self._queue = []
        self.now_playing = None
        self.want_stop = False
        self.song_start_time = None
        self.pause_start_time = None
        self.volume = .5
        self.skip_votes = []
        self.search_options = {}

    def getFormattedPlayRemainder(self):
        remainder = self.now_playing.duration - ((self.pause_start_time or time.time()) - self.song_start_time)
        return '{}:{:0>2}'.format(int(remainder / 60), int(remainder) % 60)

    def getFormattedTimeUntilQueued(self, index):
        seconds = self.now_playing.duration - ((self.pause_start_time or time.time()) - self.song_start_time)
        for i in range(index):
            seconds += self._queue[i].duration
        return get_time_from_seconds(seconds, short=True)

    def get_voice_channel(self):
        return self.voice_clients[0].channel

    def play(self, source):
        self.voice_clients[0].play(source, after=self.next_song)
        self.song_start_time = time.time()

    def next_song(self, error=None):
        if len(self._queue):
            source = self._queue.pop(0)
            self.play(source)
            self.skip_votes.clear()
            self.now_playing = source
            return source
        else:
            self.now_playing = None

    async def search(self, member, query):
        loop = asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info('ytsearch5:' + query, download=False))
        except youtube_dl.utils.DownloadError as e:
            return []

        search_options = []
        entries = data.get('entries', [data])
        for data in entries:
            search_options.append(data)
        self.search_options[member] = search_options

        return search_options

    async def queue(self, url):
        sources = await YTDLSource.from_url(url)
        prevQueueLen = len(self._queue)
        firstSource = None

        for source in sources:
            if source.error:
                return {'error': source.error}
            if not source.age_restricted:
                if not firstSource:
                    firstSource = source
                source.volume = self.volume
                self._queue.append(source)

        result = {
            'source': firstSource,
            'queue_index': prevQueueLen + 1,
            'sources_added': len(self._queue) - prevQueueLen,
            'age_restricted': len(sources) - (len(self._queue) - prevQueueLen),
            'error': None
        }

        if not self.is_playing():
            source = self.next_song()
            result['queue_index'] = 0
        return result

    def pause(self):
        self.voice_clients[0].pause()
        self.pause_start_time = time.time()

    def seek(self, time):
        new_source = YTDLSource.from_timestamp(self.now_playing, time)
        self._queue.insert(0, new_source)
        self.voice_clients[0].stop()

    def skip(self):
        self.voice_clients[0].stop()

    def stop(self):
        self._queue.clear()
        self.voice_clients[0].stop()

    def resume(self):
        self.voice_clients[0].resume()
        self.song_start_time += time.time() - self.pause_start_time
        self.pause_start_time = None

    def set_volume(self, volume):
        self.volume = volume
        self.now_playing.volume = volume
        for source in self._queue:
            source.volume = volume

    def is_playing(self):
        return self.voice_clients[0].is_playing()

    def is_paused(self):
        return self.voice_clients[0].is_paused()