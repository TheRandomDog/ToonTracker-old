import re
from discord import Color, Embed
from math import ceil
from .module import *
from extra.tunetracker import TuneTracker, YTDLSource

cde = Module.create_discord_embed
EMBED_COLOR = Color.from_rgb(228, 167, 255)

VC_MISSING = cde(subtitle=":musical_note: Please join a voice channel and I'll send a TuneTracker your way!", color=EMBED_COLOR)
VC_MISSING_BLUNT = cde(subtitle=":musical_note: Can't help you, you're not in a voice channel.", color=EMBED_COLOR)
BOT_LOADING = cde(subtitle=":minidisc: Spinning up your TuneTracker, it'll be just a bit...", color=EMBED_COLOR)
BOT_SHORTAGE = cde(subtitle=":warning: We're out of TuneTrackers! Try again a little later.", color=EMBED_COLOR)
BOT_MISSING = cde(subtitle=":musical_note: Can't help you, there's no TuneTracker in your voice channel.", color=EMBED_COLOR)

PAUSE = ":pause_button: Paused.{wanted_stop}"
PAUSE_NOTICE = ':pause_button: The player is paused.'
PAUSE_NO_ICON = 'The player is paused.'
PAUSE_REDUNDANT = ":pause_button: The player is already paused.{wanted_stop}"
PAUSE_WANTED_STOP = ' TuneTracker will stop when the voice channel is empty.'
STOP = ':stop_button: Stopped and cleared the queue.'
STOP_NOTICE = ':stop_button: The player has stopped.'
STOP_REDUNDANT = ':stop_button: The player has already stopped.'
SKIP = ':track_next: Skipped.'
SKIP_VOTE = ":ballot_box: Your vote to skip this song has been submitted! You need **{} more votes**."
SKIP_VOTED = ":no_entry_sign: You've already voted to skip this song."
AGE_RESTRICTED = ':underage: At least some of music that was linked may be inappropriate for this Discord and was not added. Please refer to the server rules in #welcome.'
QUEUE_FAILURE = ":warning: We couldn't add the music you linked. Sorry about that."
QUEUE_PLAYING = 'Your song is now playing!'
QUEUE_PLAYING_MULTIPLE = '**{} songs** were added to the queue. Your first song is now playing!'
QUEUE_LATER = 'Your song was added to the queue.'
QUEUE_LATER_MULTIPLE = "**{} songs** were added. Here's where your first song is in the queue."
VOLUME_RANGE = ':no_entry_sign: You cannot set the volume below 0 or above 100.'
VOLUME_SET = '{icon} Set volume to **{volume}%**'
VOLUME = '{icon} The volume is at **{volume}%**'
SEARCH_CHOICE_UNPROMPTED = ":no_entry_sign: Please use `~play url` or `~play search` to play a song."
SEARCH_CHOICE_RANGE = ':no_entry_sign: Please select your song choice by choosing a number between 1-5. *(e.g. `~play 1`)*'
SEARCH_NO_RESULTS = ":question: No search results were found. Please try a direct url or a new search."
SEARCH = "Please choose a song based on its number. *(e.g. `~play 1`)*"
SEEK_INVALID = ':no_entry_sign: Please format your seek in seconds or as `HH:MM:SS` *(e.g. `1:23`)*'
SEEK = "Playing from **{}**"

class MusicManager(Module):
    EMBED_COLOR = Color.from_rgb(228, 167, 255)
    EMOJI_INDEXES = {
        1: ':one:',
        2: ':two:',
        3: ':three:',
        4: ':four:',
        5: ':five:',
        6: ':six:',
        7: ':seven:',
        8: ':eight:',
        9: ':nine:',
        10: ':keycap_ten:'
    }

    class QueueCMD(Command):
        """~queue
        
            Returns the currently playing song and the music queue for your voice channel.
        """

        NAME = 'queue'

        @classmethod
        async def execute(cls, client, module, message, *args):
            if not message.author.voice:
                return VC_MISSING
            bot = module.get_bot(message.author)
            if not bot:
                return BOT_MISSING
            elif not bot.is_playing():
                embed = module.create_music_embed(
                    bot,
                    message=PAUSE_NO_ICON if bot.is_paused() else STOP_NOTICE,
                    playing=bot.now_playing if bot.is_paused() else None,
                    queued=bot._queue if bot.is_paused() else None,
                )
            else:
                embed = module.create_music_embed(
                    bot,
                    playing=bot.now_playing,
                    queued=bot._queue
                )
            await bot.get_channel(message.channel.id).send(embed=embed)

    class PlayCMD(Command):
        """~play [url | search terms>]
        
            Plays music directly from URL in your voice channel, or if search terms are provided, searches YouTube.
            A search will return 5 results, which can then be chosen with `~play #`.

            If no parameter is provided, `~play` works the same as `~continue`.
        """
        NAME = 'play'

        @classmethod
        async def execute(cls, client, module, message, *args):
            if not message.author.voice:
                return VC_MISSING

            if message.author.voice.channel.id not in module.running_bots:
                await message.channel.send(embed=BOT_LOADING)
                try:
                    bot = await module.spawn_bot(message.author.voice.channel)
                except IndexError:
                    return BOT_SHORTAGE

                await bot.get_channel(message.author.voice.channel.id).connect()
            else:
                bot = module.running_bots[message.author.voice.channel.id]

            async with bot.get_channel(message.channel.id).typing():
                if args:
                    if args[0].startswith('http'):         
                        result = await bot.queue(args[0])
                        if result['error']:
                            await bot.get_channel(message.channel.id).send(embed=module.create_music_embed(bot, message=':no_entry_sign: ' + result['error']))
                        elif result['sources_added'] == 0:
                            if result['age_restricted'] > 0:
                                await bot.get_channel(message.channel.id).send(embed=module.create_music_embed(bot, message=AGE_RESTRICTED))
                            else:
                                await bot.get_channel(message.channel.id).send(embed=module.create_music_embed(bot, message=QUEUE_FAILURE))
                        elif result['queue_index'] == 0:
                            await bot.get_channel(message.channel.id).send(
                                embed=module.create_music_embed(
                                    bot,
                                    message=(
                                        (QUEUE_PLAYING_MULTIPLE.format(result['sources_added']) if result['sources_added'] > 1 else QUEUE_PLAYING)
                                        + ('\n' + AGE_RESTRICTED if result['age_restricted'] else '')
                                    ),
                                    playing=result['source']
                                )
                            )
                        else:
                            await bot.get_channel(message.channel.id).send(
                                embed=module.create_music_embed(
                                    bot,
                                    message=(
                                        (QUEUE_LATER_MULTIPLE.format(result['sources_added']) if result['sources_added'] > 1 else QUEUE_LATER)
                                        + ('\n' + AGE_RESTRICTED if result['age_restricted'] else '')
                                    ),
                                    queued=[None for _ in range(result['queue_index'] - 1)] + [result['source']],
                                    queue_display_limit = result['queue_index'] + 1
                                )

                            )
                    elif args[0].isdigit():
                        choice = int(args[0])
                        if message.author not in bot.search_options:
                            await bot.get_channel(message.channel.id).send(embed=module.create_music_embed(bot, message=SEARCH_CHOICE_UNPROMPTED))
                        elif not 1 <= choice <= len(bot.search_options[message.author]):
                            await bot.get_channel(message.channel.id).send(embed=module.create_music_embed(bot, message=SEARCH_CHOICE_RANGE))
                        else:
                            await module.PlayCMD.execute(client, module, message, bot.search_options[message.author][choice - 1]['webpage_url'])
                            del bot.search_options[message.author]
                    else:
                        search_options = await bot.search(message.author, ' '.join(args))
                        if not search_options:
                            await bot.get_channel(message.channel.id).send(embed=module.create_music_embed(bot, message=SEARCH_NO_RESULTS))
                            if message.author in bot.search_options:
                                del bot.search_options[message.author]
                        else:
                            await bot.get_channel(message.channel.id).send(embed=module.create_music_embed(bot, message=SEARCH, search_results=search_options))
                else:
                    await module.ContinueCMD.execute(client, module, message)

    class ContinueCMD(Command):
        """~continue
            `~resume`

            Continues playing back music after being paused in your voice channel.
        """
        NAME = 'continue'

        @classmethod
        async def execute(cls, client, module, message, *args):
            if not message.author.voice:
                return VC_MISSING_BLUNT
            bot = module.get_bot(message.author)
            if not bot:
                return BOT_MISSING
            elif not bot.is_playing() and not bot.is_paused():
                await bot.get_channel(message.channel.id).send(embed=module.create_music_embed(bot, message=STOP_NOTICE))
            else:
                if not bot.is_playing():
                    bot.resume()
                await bot.get_channel(message.channel.id).send(embed=module.create_music_embed(bot, playing=bot.now_playing))
    class ResumeCMD(ContinueCMD):
        NAME = 'resume'

    class PauseCMD(Command):
        """~pause
        
            Pauses music playback in your voice channel.
        """
        NAME = 'pause'

        @classmethod
        async def execute(cls, client, module, message, *args):
            if not message.author.voice:
                return VC_MISSING_BLUNT
            bot = module.get_bot(message.author)
            if not bot:
                return BOT_MISSING
            elif bot.is_paused():
                await bot.get_channel(message.channel.id).send(
                    embed=module.create_music_embed(bot, message=PAUSE_REDUNDANT.format(wanted_stop=PAUSE_WANTED_STOP if args and args[0] == 'stop' else ''))
                )
            else:
                bot.pause()
                await bot.get_channel(message.channel.id).send(
                    embed=module.create_music_embed(bot, message=PAUSE.format(wanted_stop=PAUSE_WANTED_STOP if args and args[0] == 'stop' else ''))
                )

    class StopCMD(Command):
        """~stop
        
            Stops the music playback and clears the queue in your voice channel.

            This command only works if you're a moderator or you're the lobby owner. Otherwise, the music is paused.
        """
        NAME = 'stop'

        @classmethod
        async def execute(cls, client, module, message, *args):
            if not message.author.voice:
                return VC_MISSING_BLUNT
            bot = module.get_bot(message.author)
            if not bot:
                return BOT_MISSING
            elif bot.is_playing() or bot.is_paused():
                if Config.get_rank_of_member(message.author) >= 300 or (module.lobbies and any([l['voice_channel_id'] == bot.get_voice_channel().id for l in module.lobbies.getLobbies(owner=message.author)])):
                    bot.stop()
                    await bot.get_channel(message.channel.id).send(embed=module.create_music_embed(bot, message=STOP))
                else:
                    await module.PauseCMD.execute(client, module, message, 'stop')
            else:
                await bot.get_channel(message.channel.id).send(embed=module.create_music_embed(bot, message=STOP_REDUNDANT))

    class SkipCMD(Command):
        """~skip
        
            Skips the current music track in your voice channel.
            
            A vote will begin if you're not a moderator or a lobby owner. To vote, use this command.
        """
        NAME = 'skip'

        @classmethod
        async def execute(cls, client, module, message, *args):
            if not message.author.voice:
                return VC_MISSING_BLUNT
            bot = module.get_bot(message.author)
            if not bot:
                return BOT_MISSING
            elif bot.is_paused():
                await bot.get_channel(message.channel.id).send(embed=module.create_music_embed(bot, message=PAUSE_NOTICE))
            elif not bot.is_playing():
                await bot.get_channel(message.channel.id).send(embed=module.create_music_embed(bot, message=STOP_NOTICE))
            elif (Config.get_rank_of_member(message.author) >= 300 or (module.lobbies and any([l['voice_channel_id'] == bot.get_voice_channel().id for l in module.lobbies.getLobbies(owner=message.author)]))) \
              or (len(bot.skip_votes) + 1 >= ceil(len(bot.get_voice_channel().members) / 3) and message.author not in bot.skip_votes):
                bot.skip()
                await bot.get_channel(message.channel.id).send(embed=module.create_music_embed(bot, message=SKIP, playing=bot._queue[0] if bot._queue else None, skip=True))
            else:
                if message.author in bot.skip_votes:
                    await bot.get_channel(message.channel.id).send(embed=module.create_music_embed(bot, message=SKIP_VOTED))
                else:
                    bot.skip_votes.append(message.author)
                    await bot.get_channel(message.channel.id).send(embed=module.create_music_embed(
                        bot,
                        message=SKIP_VOTE.format(
                            ceil(len(bot.get_voice_channel().members) / 3) - len(bot.skip_votes)
                        )
                    ))

    class VolumeCMD(Command):
        """~volume [new volume (0-100)]
        
            Adjusts or returns the playback volume in your voice channel.
        """
        NAME = 'volume'

        @classmethod
        async def execute(cls, client, module, message, *args):
            if not message.author.voice:
                return VC_MISSING_BLUNT
            bot = module.get_bot(message.author)
            if not bot:
                return BOT_MISSING
            elif args:
                if (args[0].isdigit() and not 0 <= int(args[0]) <= 100) or not args[0].isdigit():
                    await bot.get_channel(message.channel.id).send(embed=module.create_music_embed(bot, message=VOLUME_RANGE))
                else:
                    volume = int(args[0])
                    bot.set_volume(volume / 100)
                    if 1 <= volume <= 35:
                        icon = ':sound:'
                    elif volume > 35:
                        icon = ':loud_sound:'
                    else:
                        icon = ':speaker:'
                    await bot.get_channel(message.channel.id).send(embed=module.create_music_embed(bot, message=VOLUME_SET.format(icon=icon, volume=volume)))
            else:
                volume = int(bot.volume * 100)
                if 1 <= volume <= 35:
                    icon = ':sound:'
                elif volume > 35:
                    icon = ':loud_sound:'
                else:
                    icon = ':speaker:'
                await bot.get_channel(message.channel.id).send(embed=module.create_music_embed(bot, message=VOLUME.format(icon=icon, volume=volume)))

    class SeekCMD(Command):
        """~seek [HH:MM:SS | seconds]
            `~jump ...
            ~time ...`
        
            Starts playing the music back at the specified time in your voice channl.
        """
        NAME = 'seek'

        @classmethod
        async def execute(cls, client, module, message, *args):
            if not message.author.voice:
                return VC_MISSING_BLUNT
            bot = module.get_bot(message.author)
            if not bot:
                return BOT_MISSING

            grammar = ''
            try:
                valid = re.match(r'(\d?\d:)?(\d?\d:)?\d\d', args[0]) or args[0].isdigit()
                if not valid:
                    raise ValueError()
                elif args[0].isdigit():
                    grammar = ' **seconds**'
            except (IndexError, ValueError) as e:
                await bot.get_channel(message.channel.id).send(embed=module.create_music_embed(bot, message=SEEK_INVALID))
                return
            if not bot.is_playing() and not bot.is_paused():
                await bot.get_channel(message.channel.id).send(embed=module.create_music_embed(bot, message=STOP_NOTICE))
                return
            bot.seek(args[0])
            await bot.get_channel(message.channel.id).send(embed=module.create_music_embed(bot, message=SEEK.format(args[0]) + grammar, playing=bot._queue[0] if bot._queue else None, skip=True))
    class JumpCMD(SeekCMD):
        NAME = 'jump'
    class TimeCMD(SeekCMD):
        NAME = 'time'

    def __init__(self, client):
        Module.__init__(self, client)

        self.available = Config.get_module_setting('music', 'bots', [])
        self.running_bots = {}
        self.lobbies = client.request_module('lobbies')

    def channel_in_lobby(self, channel):
        if lobbies:
            return lobbies.channel_in_lobby(channel)
        return False

    def create_music_embed(self, bot, *, message=Embed.Empty, playing=None, queued=None, queue_display_limit=10, search_results=None, skip=False):
        embed = Embed(color=EMBED_COLOR, description=message)
        embed.set_author(name='Voice Channel: {}'.format(bot.get_voice_channel().name))
        if playing:
            embed.add_field(
                name='{} Now Playing'.format(':arrow_forward:' if message != PAUSE_NO_ICON else ':pause_button:'),
                value='**{}** `[{} left]`'.format(playing.title, playing.getFormattedDuration() if skip else bot.getFormattedPlayRemainder())
            )
        if queued is not None:
            if queued:
                value = '\n'.join(
                    ['{} {} `[{} | {} away]`'.format(
                        self.EMOJI_INDEXES.get(queued.index(source) + 1, ':arrow_right:'),
                        source.title,
                        source.getFormattedDuration(),
                        bot.getFormattedTimeUntilQueued(queued.index(source))
                    ) for source in queued[:queue_display_limit] if source])
                if len(queued) > queue_display_limit:
                    value += '\n:arrow_right: ...and more `[{} total | {} away]`'.format(
                        YTDLSource.getSpecificFormattedDuration(sum([source.duration for source in queued[queue_display_limit:]])),
                        bot.getFormattedTimeUntilQueued(queue_display_limit)
                    )
            else:
                value = 'Nothing.'
            embed.add_field(
                name=':fast_forward: Coming Soon',
                value=value,
                inline=False
            )
        if search_results:
            value = '\n'.join(
                ['{} {} `[{}]`'.format(
                    self.EMOJI_INDEXES.get(search_results.index(result) + 1, ':arrow_right:'),
                    result['title'],
                    YTDLSource.getSpecificFormattedDuration(result['duration'])
                ) for result in search_results])
            embed.add_field(
                name=':mag: Search Results',
                value=value,
                inline=False
            )

        return embed

    def get_bot(self, member):
        if member.voice:
            return self.running_bots.get(member.voice.channel.id, None)

    async def spawn_bot(self, channel):
        token = self.available.pop()
        bot = TuneTracker()
        bot.EMOJI_INDEXES = self.EMOJI_INDEXES
        self.client.loop.create_task(bot.start(token))
        await bot.wait_until_ready()
        self.running_bots[channel.id] = bot
        return bot

module = MusicManager