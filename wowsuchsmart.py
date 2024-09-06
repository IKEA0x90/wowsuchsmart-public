import interactions
from interactions import listen
from services import assistant

bot = interactions.Client(intents=interactions.Intents.ALL, send_command_tracebacks=False) 

@listen()
async def on_message_create(event):

    if (event.message.author == bot.user):
        return
    
    content = event.message.content.strip()
    channel = event.message.channel
    
    #try: 
    if not isinstance(channel, interactions.ThreadChannel):
        if content.startswith("!wow"):
            command = content[5:]
        else:
            return

        if command:
            thread_name = 101 * "-";
            while len(thread_name) > 100 or thread_name.startswith("wowsuchsmart-cat-"):
                thread_name_prompt = [{"role": "system", "content": "Make a title for a chat based on the prompt. It must be relatively short. It must be relevant to the message. Only respond with the title. The prompt is: " + command}]
                thread_name = await assistant.get_single_response(thread_name_prompt)
                print(f"Thread name generated for {command} was {thread_name}.")
                thread = await channel.create_thread(name=thread_name, auto_archive_duration=60, message=event.message)
    
            response = await assistant.get_thread_response(event.message)
            await thread.send(response.get("id"))
            for m in response.get("content"):
                await thread.send(m)
            return
    else:
        id = ""
        async for m in channel.history(limit=2, after=channel.id):
            id = m.content
        if channel.owner_id == bot.user.id:
            response = await assistant.get_thread_response(event.message, id)
        else:
            return

        for m in response.get("content"):
            await event.message.channel.send(m)
        return
    
    return
    #except Exception as e:
        #await channel.send(f"{e.__class__.__name__}")
    
bot.start('')
