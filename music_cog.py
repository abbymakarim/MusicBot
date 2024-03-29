import discord
import asyncio
from discord.ext import commands
from asyncio import sleep
from yt_dlp import YoutubeDL

from dotenv import load_dotenv

load_dotenv() 
from dotenv import dotenv_values
config = dotenv_values(".env")

class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music_title = ''
        self.song = []

        self.is_playing = False
        self.is_disconnected = False
        self.is_paused = False

        self.YDL_OPTIONS = {'format': 'bestaudio/best', 'acodec' 'noplaylist': 'True', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

        self.vc = None

    async def search_yt(self, songName, voiceChannel):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info("ytsearch:%s" % songName, download=False)['entries'][0]
                for i in info['formats']:
                    if (i['ext']) == 'm4a':
                        url = i['url']
                        break
            except Exception:
                return False
            sourceSong = {'source': url, 'title': info['title'], 'voiceChannel': voiceChannel}
            self.song.append(sourceSong)
            return {'source': url, 'title': info['title']}

    def play_next(self):
        if len(self.song) > 0:
            self.is_playing = True
            songDetails = self.song[0]
            m_url = songDetails.get('source')
            self.music_title = songDetails.get('title')

            self.song.pop(0)
            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    async def play_music(self, ctx):
        if len(self.song) > 0:
            self.is_playing = True
            songDetails = self.song[0]
            m_url = songDetails.get('source')

            if self.vc == None or not self.vc.is_connected():
                self.vc = await ctx.author.voice.channel.connect()

                if self.vc == None:
                    await ctx.send("Could not connect to the voice channel")
                    return
            else:
                await self.vc.move_to(ctx.author.voice.channel)

            self.music_title = songDetails.get('title')

            self.song.pop(0)

            # need to fix this logic for playing music
            try:
                self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
                while self.vc.is_playing():
                    if self.music_title != '':
                        await ctx.send('```Currently Playing: '+ self.music_title + '```')
                        self.music_title = ''
                        self.is_disconnected = False
                    await sleep(1) 
                        # Ini masih auto dc kalau lagu abis ga nunggu (perlu adjustment)
                await ctx.send("```No more song in queue```")
                if self.vc.is_playing() == False:
                    self.is_disconnected = True
                await ctx.send("```Stand by...```")
                await sleep(10) 
                if self.is_disconnected == True:
                    await self.vc.disconnect()
            except Exception:
                log_channel = self.bot.get_channel(config['LOG_CHANNEL_ID'])
                await log_channel.send("```Could not play the song. Ask opik for advice```")
                await self.vc.disconnect()
        else:
            self.is_playing = False

    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx, *args):
        query = " ".join(args)

        voice_channel = ctx.author.voice.channel    
        if voice_channel is None:
            await ctx.send("Connect to a voice channel!")
        elif self.is_paused:
            self.vc.resume()
        else:
            await ctx.send("```Searching....```")
            song = await self.search_yt(query, voice_channel);
            await ctx.send("```Song added to the queue : "+ song['title'] + "```")
            if self.is_playing == False:
                await self.play_music(ctx)

    @commands.command(name="pause", help="Pauses the current song being played")
    async def pause(self, ctx, *args):
        if self.is_playing:
            self.is_playing = False
            self.is_paused = True
            self.vc.pause()
        elif self.is_paused:
            self.is_playing = True
            self.is_paused = False
            self.vc.resume()

    @commands.command(name="resume", aliases=["r"], help="Resumes playing the current song")
    async def resume(self, ctx, *args):
        if self.is_paused:
            self.is_playing = True
            self.is_paused = False
            self.vc.resume()

    @commands.command(name="skip", aliases=["s"], help = "Skips the currently played song")
    async def skip(self, ctx, *args):
        if self.vc != None and self.vc:
            self.vc.stop()
            await self.play_music(ctx)

    @commands.command(name="queue", aliases=["q"], help="Displays all the songs currently in the queue")
    async def queue(self, ctx):
        retval = ""

        for i in range(0, len(self.song)):
            if i > 4: break
            songDetails = self.song[i]
            retval += songDetails.get('title') + '\n'

        if retval != "":
            await ctx.send(retval)
        else:
            await ctx.send("No music in the queue.")

    @commands.command(name="clear", aliases=["c", "bin"], help="Clears the queue")
    async def clear(self, ctx, *args):
        self.song = []
        await ctx.send("Music queue cleared")

    @commands.command(name="leave", aliases=["disconnect", "l", "d"], help="Kick the bot from the voice channel")
    async def leave(self, ctx):
        self.is_playing = False
        self.is_paused = False
        await self.vc.disconnect()
