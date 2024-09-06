import interactions
from interactions import listen, slash_command, slash_option

from rolling import captcha, cards, other
from services import command_parsing
from services import persistence

bot = interactions.Client(intents=interactions.Intents.ALL, send_command_tracebacks=False, debug_scope=683335588618960927) 

global data
data = {}

@listen()
async def on_message_create(event):
    global data
    if (event.message.author == bot.user):
        return
    
    content = event.message.content.strip()
    channel = event.message.channel

    if content.startswith("!"):
        content = content[1:]

        if content == "r":
            content = "d20"

        roll = command_parsing.parse_command(content, event.message.author)
        if roll:
            await channel.send(roll)
            return
        else:
            return

    if (isinstance(channel, interactions.ThreadChannel)):
        
        if channel.name == "Deck" and channel.owner_id == bot.user.id:
            if content.isdigit():
                amount = command_parsing.parse_command(str(int(content)), used_by="number")

                try:
                    deck = await data.get_deck(str(channel.id))
                except TypeError:
                    deck = data.get_deck(str(channel.id))
                
                if deck:
                    pulled_cards = deck.pull_card(amount)

                    for card in pulled_cards:
                        embed, file = card.get_embed()
                        await channel.send(file=file, embed=embed)

                    data.update_deck(deck)
                    deleted = await cards.save(deck)
                    if deleted:
                        await channel.send("This deck is now empty! The thread will be deleted on your next message")
                        
                else:
                    await channel.delete(reason="Deck is empty")
            else:
                await channel.send(f"Provide the number of cards you wish to pull")
        return

    return

@slash_command(name="r", description="Roll dice")
@slash_option(
    name="dice",
    description="Dice to use",
    opt_type=interactions.OptionType.STRING,	
)
async def r(ctx: interactions.SlashContext, dice = "d20"):
    roll = command_parsing.parse_command(dice, ctx.author)
    if roll:
        await ctx.send(roll)
    else: 
        await ctx.send(f"Couldn't parse {dice}")

@slash_command(name="roulette", description="Spin the wheel")
async def roulette(ctx: interactions.SlashContext):
    roll = await other.roulette()
    await ctx.send(roll)

@slash_command(name="deck", description="Create a deck of cards")
@slash_option(
    name="deck_option",
    description="Deck of cards",
    required=True,
    opt_type=interactions.OptionType.STRING,
    choices=[
        interactions.SlashCommandChoice(name=f"{cards.Deck.get_name(cards.Deck.DECKNAMES.FULL)}", value=f"{cards.Deck.DECKNAMES.FULL}"),
        interactions.SlashCommandChoice(name=f"{cards.Deck.get_name(cards.Deck.DECKNAMES.TAROT)}", value=f"{cards.Deck.DECKNAMES.TAROT}"),
        interactions.SlashCommandChoice(name=f"{cards.Deck.get_name(cards.Deck.DECKNAMES.TAROTMAJOR)}", value=f"{cards.Deck.DECKNAMES.TAROTMAJOR}"),
        interactions.SlashCommandChoice(name=f"{cards.Deck.get_name(cards.Deck.DECKNAMES.MANYTHINGSFULL)}", value=f"{cards.Deck.DECKNAMES.MANYTHINGSFULL}"),
        interactions.SlashCommandChoice(name=f"{cards.Deck.get_name(cards.Deck.DECKNAMES.MANYTHINGSPARTIAL)}", value=f"{cards.Deck.DECKNAMES.MANYTHINGSPARTIAL}"),
    ]
)
async def deck(ctx: interactions.SlashContext, deck_option: str):
    global data
    message = await ctx.send(f"Here is your {cards.Deck.get_name(deck_option).lower()}")
    thread_name = "Deck"
    thread = await ctx.channel.create_thread(name=thread_name, auto_archive_duration=60, message=message)
    deck = cards.Deck(deck_option, str(thread.id), cards.Deck.generate_deck(deck_option))
    data.decks["id"] = deck
    await cards.save(deck)
    await thread.send("Please enter the number of cards you wish to pull")

@slash_command(name="void", description="Use Void of Probability")
async def void(ctx: interactions.SlashContext):
    await ctx.defer()

    await captcha.generate_captcha(300, 100, 6)

    with open("./storage/captcha.txt", "r") as f:
        captcha_text = f.read()

    button = interactions.Button(
        custom_id="solve_button",
        style=interactions.ButtonStyle.SECONDARY,
        label="Solve"
    )
    message = await ctx.send(file=interactions.File('./storage/captcha.png'), components=button)

    try:
        used_component = await bot.wait_for_component(components=button, timeout=20)
    except TimeoutError:
        print(f"Captcha {captcha_text} timed out")
        button.disabled = True
        await message.edit(components=button)
        await message.reply(content=f"```Access Denied```")
    else:

        response = interactions.Modal(
            interactions.ShortText(label="Solution", custom_id="solution"),
            title="Void of Probability",
        )
        await used_component.ctx.send_modal(modal=response)
        modal_ctx: interactions.ModalContext = await ctx.bot.wait_for_modal(response)
        solution = modal_ctx.responses["solution"]
        
        if solution == captcha_text:
            await modal_ctx.send(f"```Access Granted```")
            print(f"Captcha {captcha_text} solved")
        else:
            await modal_ctx.send(f"```Access Denied```")
            print(f"Captcha {captcha_text} failed")
        
        button.disabled = True
        await message.edit(components=button)

@slash_command(name="shuffle", description="Shuffle around some values")
@slash_option(
    name="ac",
    description="ac",
    opt_type=interactions.OptionType.STRING,
    required=True	
)
@slash_option(
    name="prf",
    description="prf",
    opt_type=interactions.OptionType.STRING,
    required=True	
)
@slash_option(
    name="spd",
    description="spd",
    opt_type=interactions.OptionType.STRING,
    required=True	
)
@slash_option(
    name="str",
    description="str",
    opt_type=interactions.OptionType.STRING,
    required=True	
)
@slash_option(
    name="dex",
    description="dex",
    opt_type=interactions.OptionType.STRING,
    required=True	
)
@slash_option(
    name="con",
    description="con",
    opt_type=interactions.OptionType.STRING,
    required=True	
)
@slash_option(
    name="int",
    description="int",
    opt_type=interactions.OptionType.STRING,
    required=True	
)
@slash_option(
    name="wis",
    description="wis",
    opt_type=interactions.OptionType.STRING,
    required=True	
)
@slash_option(
    name="cha",
    description="cha",
    opt_type=interactions.OptionType.STRING,
    required=True	
)
async def shuffle(ctx: interactions.SlashContext, ac, prf, spd, str, dex, con, int, wis, cha):
    values = await other.randostats(ac, prf, spd, str, dex, con, int, wis, cha)
    await ctx.send(f"```ac: {values['ac']}, prf: {values['prf']}, spd: {values['spd']}\nstr: {values['str']}, dex: {values['dex']}, con: {values['con']}, int: {values['int']}, wis: {values['wis']}, cha: {values['cha']}```")

@slash_command(
    name="replacements", 
    description="Add, remove or get replacements", 
)
@slash_option(
    name="mode",
    description="What to do",
    required=True,
    opt_type=interactions.OptionType.STRING,
    choices=[
        interactions.SlashCommandChoice(name="add", value="add"),
        interactions.SlashCommandChoice(name="remove", value="remove"),
        interactions.SlashCommandChoice(name="get", value="get"),
        interactions.SlashCommandChoice(name="toggle", value="toggle"),
    ]
)
@slash_option(
    name="original",
    description="Original value",
    opt_type=interactions.OptionType.STRING,
)
@slash_option(
    name="replacer",
    description="Replacement value",
    opt_type=interactions.OptionType.STRING,
)
@interactions.check(interactions.is_owner())
async def replacements(ctx: interactions.SlashContext, mode, original = None, replacer = None):
    global data
    if mode == "get":
        await ctx.send(f"{data.replacements}", ephemeral=True)
        return
        
    if mode == "add" and original is not None and replacer is not None:
        data.add_replacer(original, replacer)
        await ctx.send(f"Added replacement {original} -> {replacer}", ephemeral=True)
        await save()
        return

    if mode == "remove" and original is not None:
        data.remove_replacer(original)
        await ctx.send(f"Removed replacement for {original}", ephemeral=True)
        await save()
        return
    
    if mode == "toggle":
        data.toggle_replacements()
        await ctx.send(f"Replacements toggled {'on' if data.get_replacements_active() else 'off'}", ephemeral=True)
        await save()
        return

@slash_command(
    name="forced_roll", 
    description="Force the next roll", 
)
@slash_option(
    name="outcome",
    description="Desired outcome",
    required=True,
    opt_type=interactions.OptionType.INTEGER,
)
@interactions.check(interactions.is_owner())
async def ring(ctx: interactions.SlashContext, outcome):
    global data
    data.add_forced_roll(outcome)
    persistence.save(data)
    await ctx.send(f"Added forced roll {outcome}", ephemeral=True)

#@interactions.Task.create(interactions.IntervalTrigger(minutes=10))
async def save():
    global data
    persistence.save(data)

@listen()
async def on_startup():
    global data
    data = persistence.load()
    #save.start()
    await save()

bot.start('')