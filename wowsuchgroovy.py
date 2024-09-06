from asyncio import sleep
import asyncio
from functools import partial
import os
from pathlib import Path
import random
from fuzzywuzzy import fuzz
import interactions
from interactions import slash_command, slash_option, check, is_owner
from interactions.api.voice.audio import Audio
from interactions.ext.paginators import Paginator
from mutagen.easyid3 import EasyID3
import pickle

bot = interactions.Client(intents=interactions.Intents.ALL, send_command_tracebacks=False, disable_dm_commands=True)

queue = []
loop_song = False
loop_queue = False
streaming = False
looper = False

class Song:
    def __init__(self, filename, link = False):
        self.filename = filename
        self.link = link

        if not self.link:
            tags = {}
            try:
                audio = EasyID3(filename)
                for tag in audio:
                    tags[tag] = audio[tag][0]
            except:
                print(f"Something wrong with {filename}")
            
            self.title = None
            self.artist = None
            self.number = None

            if "title" in tags:
                self.title = tags["title"]
            else:
                self.title = filename

            if "artist" in tags:
                self.artist = tags["artist"]

            if "tracknumber" in tags:
                if tags["tracknumber"].isnumeric():
                    self.number = int(tags["tracknumber"])
        else:
            self.title = self.link

    def __str__(self):
        return self.title if not self.artist else f"{self.title} by {self.artist}" 

    def __lt__(self, other):
        if isinstance(other, Song):
            if self.number is None:
                return False
            elif other.number is None:
                return True
            else:
                return self.number < other.number
        return NotImplemented

    def make_embed(self):
        embed = None
        embed = interactions.Embed(title=f"{self.title}")
        if self.artist:
            embed.set_author(name=f"{self.artist}")
        return embed
    
    @staticmethod
    def make_embed_static(tags):
        embed = None
        if "title" in tags:
            embed = interactions.Embed(title=f"{tags['title']}")
            if "artist" in tags:
                embed.set_author(name=f"{tags['artist']}")
        return embed

async def check_voice(ctx):
    if not ctx.author.voice:
        await ctx.send(f"Please connect to a voice channel")
        return False
    return True
    
async def queue_callback(ctx, paginator):
    song_index = paginator.page_index
    song = queue.pop(song_index)
    queue.insert(0, song)
    await ctx.send(f"{song} will play next")

async def delete_queue_callback(ctx):
    await ctx.message.delete()

def parse_remove_range(s):
    s = s.strip().replace(' ', '')
    parts = s.split(',')
    output = []

    try:
        # Parse each part individually
        for part in parts:
            if '-' in part:
                # Part is a range
                range_parts = part.split('-')
                if len(range_parts) != 2:
                    raise ValueError
                output.extend(list(range(int(range_parts[0]) - 1, int(range_parts[1]))))
            else:
                # Part is an individual number
                output.append(int(part) - 1)
    except ValueError:
        return []

    output = sorted(list(set(output)))

    return output

def search(dir, song_name, max_len, search_for_files = True):
    matches = []

    for root, dirs, files in os.walk(dir):
        search_elements = files if search_for_files else dirs
        for element in search_elements:
            match_score = fuzz.partial_ratio(song_name.lower(), element.lower())
            if match_score > 50:
                full_path = Path(root, element)  
                full_path = str(full_path).replace("\\", "/")
                matches.append((full_path, match_score))

    matches.sort(key=lambda x: x[1], reverse=True)
    return [file for file, score in matches[:max_len]]

def list_directories(path, indent=0):
    result = ''
    if os.path.exists(path):
        for item in os.listdir(path):
            new_path = os.path.join(path, item)
            if os.path.isdir(new_path):
                result += (' ' * indent) + item + '/' + '\n'
                result += list_directories(new_path, indent + 2)
    return result

def add_songs(dir, play_next):
    songs = []
    for filename in os.listdir(dir):
        if (not filename.endswith(".mp3")) or not filename[:-4]:
            continue

        songs.append(Song(f"{dir}/{filename}"))

        songs = sorted(songs, reverse=play_next)
    for song in songs:
        queue.insert(0 if play_next else len(queue), song)
    return 

async def change_activity(song: Song = None, name: str = ""):
    if song:
        activity = interactions.Activity.create(name=song.title, type=interactions.ActivityType.LISTENING)
        await bot.change_presence(activity=activity)
    elif name:
        activity = interactions.Activity.create(name=name, type=interactions.ActivityType.LISTENING)
        await bot.change_presence(activity=activity)
    else:
        await bot.change_presence()


@slash_command(name="soundpad", description="Soundpad")
@slash_option(
    name="session",
    description="Is session active or not.",
    opt_type=interactions.OptionType.BOOLEAN,
)
@check(is_owner())
async def soundpad(ctx: interactions.SlashContext, session=True):
    global streaming
    global looper
    looper = session

    if not await check_voice(ctx):
        return

    if not ctx.voice_state:
        await ctx.author.voice.channel.connect()
    
    if streaming:
        streaming = False
        await ctx.voice_state.stop()

    await ctx.send("Soundpad", ephemeral=True)
    while looper:
        try:
            with open("audio/sounds", 'r') as file:
                song = file.read().strip()
                if song:
                    if song == "#STOP":
                        looper = False
                        with open("audio/sounds", 'w') as file:
                            file.write('')
                        return
                    try:
                        song = f"audio/soundpad/{song}".replace("\\", "/")
                        audio = Audio(f"{song}")

                        if ctx.voice_state:
                            await ctx.voice_state.play(audio)
                        else:
                            return
                    except:
                        print(f"Something wrong with {song}")

                    with open("audio/sounds", 'w') as file:
                        file.write('')
        except FileNotFoundError:
            pass
        
        await asyncio.sleep(1)  # Wait for 1 second before checking again

@slash_command(name="tree", description="Display the directory tree and available stream options")
async def search_dir(ctx: interactions.SlashContext):
    dir = "audio"
    tree = list_directories(dir, 0)
    await ctx.send(f"```{tree}```")

@slash_command(name="adddir", description="Add all songs from a directory to the queue")
@slash_option(
    name="dir",
    description="Directory containing the songs",
    opt_type=interactions.OptionType.STRING,
    required=True,
)
@slash_option(
    name="play_next",
    description="Add at the start of the queue?",
    opt_type=interactions.OptionType.BOOLEAN,
)
async def adddir(ctx: interactions.SlashContext, dir, play_next = False):
    dir_name = dir
    dir = "audio/" + dir
    
    if not os.path.isdir(dir):
    
        dirs = search("audio", dir_name, 7, False)

        if not dirs:
            await ctx.send("No matching directories found")
            return
        
        if len(dirs) == 1:
            add_songs(dirs[0], play_next)
            await ctx.send(f"Added songs from {dirs[0]} to the queue")
            return
        
        dirs = [dir for dir in dirs]
        dir_selector = interactions.StringSelectMenu(
            dirs,
            placeholder="Directory",
            min_values=1,
            max_values=1,
            custom_id="dir_selector",
        )
        await ctx.send("Select the directory you wish to add songs from", components=dir_selector)

        try:
            used_component = await bot.wait_for_component(components=dir_selector, timeout=60)

        except TimeoutError:
            dir_selector.disabled = True
            await ctx.edit(components=dir_selector)

        else:
            selected_dirs = used_component.ctx.values
            for dir in selected_dirs:
                add_songs(dir, play_next)
                await used_component.ctx.send(f"Added songs from {dir} to the queue")
            dir_selector.disabled = True
            await ctx.edit(components=dir_selector)
    else: 
        add_songs(dir, play_next)
        await ctx.send(f"Added songs from {dir} to the queue")

@slash_command(name="add", description="Add a song from a directory to the queue")
@slash_option(
    name="song_name",
    description="Song to play",
    opt_type=interactions.OptionType.STRING,
    required=True,
)
@slash_option(
    name="play_next",
    description="Add at the start of the list?",
    opt_type=interactions.OptionType.BOOLEAN,
)
async def add(ctx: interactions.SlashContext, song_name, play_next = False):
    dir = "audio/"
    is_link = (song_name[:4] == "http")

    if not is_link:
        songs = search(dir, song_name, 7)

        if not songs:
            await ctx.send("No matching songs found")
            return
        
        if len(songs) == 1:
            song = Song(f"{songs[0]}")
            queue.insert(0 if play_next else len(queue), song)
            await ctx.send(f"Added {song} to the queue")
            return

        songs = [Song(f"{song}") for song in songs]
        songs = {str(song):song for song in songs}
        song_selector = interactions.StringSelectMenu(
            [f"{song}" for song in songs.values()],
            placeholder="Song",
            min_values=1,
            max_values=1,
            custom_id="song_selector",
        )
        await ctx.send("Select the song you wish to add", components=song_selector)
        try:
            used_component = await bot.wait_for_component(components=song_selector, timeout=60)
        except TimeoutError:
            song_selector.disabled = True
            await ctx.edit(components=song_selector)
        else:
            selected_songs = used_component.ctx.values
            for song in selected_songs:
                queue.insert(0 if play_next else len(queue), songs[song])
                await used_component.ctx.send(f"Added {song} to the queue")
            song_selector.disabled = True
            await ctx.edit(components=song_selector)
    else:
        song = Song(song_name, link=True)
        queue.insert(0 if play_next else len(queue), song)
        await ctx.send("Song added")

@slash_command(name="remove", description="Remove songs from the queue. Removes next song by default")
@slash_option(
    name="positions",
    description="All the indexes you wish to remove. May include ranges. Ex: 1,2,4-8,21,24-50",
    opt_type=interactions.OptionType.STRING,
)
async def remove(ctx: interactions.SlashContext, positions = "1"):
    global queue
    position_list = parse_remove_range(positions)
    if not position_list:
        await ctx.send(f"There was an error parsing {positions}")
        return 
    
    queue = [e for i, e in enumerate(queue) if i not in position_list]
    await ctx.send(f"Removed songs {positions}")

@slash_command(name="clear", description="Removes all the songs from the queue")
async def clear(ctx: interactions.SlashContext):
    queue.clear()
    await ctx.send(f"Cleared the queue")

    if ctx.voice_state:
        await ctx.voice_state.stop()

    await change_activity()

@slash_command(name="play", description="Play the queue")
async def play(ctx: interactions.SlashContext):
    global streaming
    if not await check_voice(ctx):
        return

    if not ctx.voice_state:
        await ctx.author.voice.channel.connect()

    if not queue:
        await ctx.send("Queue is empty")
        return
    
    if streaming:
        streaming = False
        await ctx.voice_state.stop()

    await ctx.send("Starting playback")
    while queue:
        song = queue.pop(0)
        try:
            audio = Audio(song.filename)

            if loop_song:
                queue.insert(0, song)
            if loop_queue:
                queue.append(song)

            if not song.link:
                await change_activity(song=song)
            else:
                await change_activity(name="???")

            if ctx.voice_state:
                await ctx.voice_state.play(audio)
            else:
                await change_activity()
                queue.insert(0, song)
                return

        except:
            print(f"Something wrong with {song}") 
    
    await change_activity()

@slash_command(name="shuffle", description="Shuffle the queue once")
async def shuffle(ctx: interactions.SlashContext):
    await ctx.send("Queue has been shuffled")
    random.shuffle(queue)

@slash_command(name="loop", description="Loop current song or the queue")
@slash_option(
    name="mode",
    description="Loop mode",
    opt_type=interactions.OptionType.STRING,
    choices=[
        interactions.SlashCommandChoice(name="off", value="off"),
        interactions.SlashCommandChoice(name="song", value="song"),
        interactions.SlashCommandChoice(name="queue", value="queue"),
    ]
)
async def loop(ctx: interactions.SlashContext, mode = "off"):
    global loop_song
    global loop_queue

    if ctx.voice_state:
            song = ctx.voice_state.current_audio.source
            song = Song(song)

    if song and (loop_song or loop_queue): 
        if loop_song:
            queue.pop(0)
        elif loop_queue:
            queue.pop(len(queue) - 1)

    loop_queue = False
    loop_song = False

    if mode == "song":
        loop_queue = False
        loop_song = True
        if song: 
            queue.insert(0, song)

    elif mode == "queue":
        loop_queue = True
        loop_song = False
        if song: 
            queue.append(song)

    await ctx.send(f"Looping set to {mode}")

@slash_command(name="skip", description="Skip the song that's currently playing")
async def skip(ctx: interactions.SlashContext):
    global streaming
    await check_voice(ctx)
    
    if not ctx.voice_state:
        await ctx.send("Playback not started")
        return
    
    if streaming:
        await ctx.send("Can't skip stream")
        return
    
    song = ctx.voice_state.current_audio.source
    song = Song(song)
    
    await ctx.voice_state.stop()
    await ctx.send(f"Skipping {song}")

@slash_command(name="stop", description="Stop playback")
async def stop(ctx: interactions.SlashContext):
    global streaming
    if not ctx.voice_state:
        await ctx.send("Nothing is playing")
        return
    
    streaming = False
    await change_activity()
    await ctx.voice_state.stop()
    await ctx.send("Stopping playback")
    return

@slash_command(name="p", description="Pause or resume playback")
async def p(ctx: interactions.SlashContext):
    await check_voice(ctx)

    if not ctx.voice_state:
        await ctx.send("Playback not started or already paused")
        return
    
    if not ctx.voice_state.paused:
        await ctx.send("Pausing playback. Use /p again to resume")
        ctx.voice_state.pause()
        return
    else:
        await ctx.send("Resuming playback")
        ctx.voice_state.resume()

@slash_command(name="np", description="Return the song that's currently playing")
async def np(ctx: interactions.SlashContext):
    await check_voice(ctx)

    if streaming:
        await ctx.send(streaming)
        return

    try:
        song = ctx.voice_state.current_audio.source
        audio = EasyID3(song)
    except:
        await ctx.send("Something went wrong")
        return

    tags = {}
    for tag in audio:
        tags[tag] = audio[tag][0]

    embed = Song.make_embed_static(tags)
    if embed:
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"```{song}```")

@slash_command(name="q", description="Display a nicely formatted version of the queue")
async def q(ctx: interactions.SlashContext):
    embeds = []
    for song in queue:
        embeds.append(song.make_embed())
    if embeds:
        paginator = Paginator.create_from_embeds(bot, *embeds)

        if len(embeds) <= 25: 
            paginator.show_select_menu = True

        paginator.show_callback_button = True
        paginator.callback = partial(queue_callback, paginator=paginator)

        await paginator.send(ctx)
        return
    
    await ctx.send("Queue is empty") 

@slash_command(name="queue", description="Display all songs in the queue")
async def q_long(ctx: interactions.SlashContext):
    pages = []
    for i in range(0, len(queue)):
        pages.append(f"{i}. {queue[i]}")
    if pages:
        paginator = Paginator.create_from_list(bot, pages)

        paginator.callback_button_emoji="🗑️"
        paginator.show_callback_button=True
        paginator.callback = delete_queue_callback

        await paginator.send(ctx)
        return
    
    await ctx.send("Queue is empty")

@slash_command(name="stream", description="Stream something or play an audio from a link")
@slash_option(
    name="source",
    description="Source of the stream",
    opt_type=interactions.OptionType.STRING,
    required=True,
    autocomplete=True
)
async def stream(ctx: interactions.SlashContext, source):
    global streaming
    source = eval(source)
    url = source["url"]
    name = source["name"]
    if not await check_voice(ctx):
        return

    if not ctx.voice_state:
        await ctx.author.voice.channel.connect()

    '''
    if ctx.voice_state.playing and not streaming:
        yes = interactions.Button(
            style=interactions.ButtonStyle.GREEN,
            label="Yes",
            disabled=False,
        )
        
        message = await ctx.send("Queue is playing. Are you sure? Queue will be saved, use /load to restore it", components=yes)
        try:
            used_component = await bot.wait_for_component(components=yes, timeout=30)
        except TimeoutError:
            yes.disabled = True
            await message.edit(components=yes)
            used_component.ctx.send("Aborting")
            return
        else:
            await save(used_component.ctx)
            await ctx.voice_state.stop()
            streaming = False
    '''
    
    try:
        streaming = name
        await change_activity(name=name)
        await ctx.send("Starting playback")
        audio = Audio(url)
        audio.locked_stream = True
        await ctx.voice_state.play(audio)
    except:
        ctx.send("Something went wrong")

@stream.autocomplete("source")
async def autocomplete(ctx: interactions.AutocompleteContext):
    user_input = ctx.input_text 

    await ctx.send(
        choices=[
            {
                "name": f"Custom: {user_input}",
                "value": {"name":"???", "url": user_input},
            },
            {
                "name": f"Retro FM",
                "value": {"name":"Retro FM", "url": "https://retro.hostingradio.ru:8043/retro256.mp3"},
            },
            {
                "name": f"Europa Plus",
                "value": {"name":"Europa Plus", "url": "http://ep256.hostingradio.ru:8052/europaplus256.mp3"},
            },
            {
                "name": f"Deep House Lounge",
                "value": {"name":"Deep House Lounge", "url": "http://198.15.94.34:8006/stream"},
            },
        ]
    )

@slash_command(name="save", description="Saves the queue to persistent memory")
async def save(ctx: interactions.SlashContext):
    with open('audio/queue', 'wb') as f:
        pickle.dump(queue, f)
    await ctx.send("Queue saved")

@slash_command(name="load", description="Loads the queue from persistent memory. Overwrites current queue")
async def load(ctx: interactions.SlashContext):
    global queue
    with open('audio/queue', 'rb') as f:
        queue = pickle.load(f)
    await ctx.send("Queue loaded")

@interactions.listen(interactions.events.VoiceUserLeave)
async def leave(event):
    global streaming

    if event.author.id == bot.user.id:
        return

    try:
        channel = bot.get_channel(event.channel.id)
        if channel and set(member.id for member in channel.voice_members) == {bot.user.id}:
            await sleep(60)
            if set(member.id for member in channel.voice_members) == {bot.user.id}:
                streaming = False
                if channel.voice_state.playing:
                    await channel.voice_state.stop()
                await channel.disconnect()
                await change_activity()
    except interactions.client.errors.VoiceNotConnected:
        return

@interactions.listen(interactions.events.VoiceUserMove)
async def move(event):
    global streaming

    if event.author.id == bot.user.id:
        return

    try:
        channel = bot.get_channel(event.previous_channel.id)
        if channel and set(member.id for member in channel.voice_members) == {bot.user.id}:
            await sleep(60)
            if set(member.id for member in channel.voice_members) == {bot.user.id}:
                if channel.voice_state.playing:
                    await channel.voice_state.stop()
                streaming = False
                await channel.disconnect()
                await change_activity()
    except interactions.client.errors.VoiceNotConnected:
        return

bot.start('')