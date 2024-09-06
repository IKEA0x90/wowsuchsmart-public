from asyncio import sleep
import base64
import json
import openai
from services import image_generation
from services.command_parsing import paginate

clientopenai = openai.OpenAI(api_key="")
assistant = clientopenai.beta.assistants.retrieve("")

async def get_thread_response(message, id = 0):
  if not id:
    thread = clientopenai.beta.threads.create()
  else:
    thread = clientopenai.beta.threads.retrieve(id)

  thread_id = thread.id
  
  content = [{"type": "text", "text": message.content}]

  if message.attachments and await is_image(message.attachments[0]):
    image = message.attachments[0]
    link = await parse_link(image)
    content.append({"type": "image_url", "image_url": {"url": link}})

  clientopenai.beta.threads.messages.create(
    thread_id=thread_id,
    role="user",
    content=content
  )

  run = clientopenai.beta.threads.runs.create(
    thread_id=thread_id,
    assistant_id=assistant.id,
  )

  while (1):
    await sleep(0.25)

    run = clientopenai.beta.threads.runs.retrieve(
      thread_id=thread_id,
      run_id=run.id
    )

    image_content = None

    if run.status == "completed":
      if image_content:
        clientopenai.beta.threads.messages.create(
          thread_id=thread_id,
          role="assistant",
          content=image_content
        )
      break;
    
    elif run.status == "in_progress":
      pass
    
    elif run.status == "requires_action":
        tools = run.required_action.submit_tool_outputs.tool_calls
        for tool in tools:
          name = tool.function.name
          args = json.loads(tool.function.arguments)

          tool_outputs=[]

          if name == "make_image":
            print(f"Used make_image with {args.get('image_description')}")
            response = await image_generation.make_image(args.get("image_description"))
            image_path = await image_generation.save_image(response)
            link = await image_generation.upload_image('', '', '', image_path)

          tool_outputs.append({"tool_call_id": tool.id, "output": link})

        clientopenai.beta.threads.runs.submit_tool_outputs(
          thread_id=thread_id,
          run_id=run.id,
          tool_outputs=tool_outputs
        )
          
    else:
      return
    
  messages = clientopenai.beta.threads.messages.list(thread_id=thread_id)

  response = messages.data[0].content[0].text.value

  paginated = paginate(response)
  response = {"id":thread_id, "content":paginated}
    
  return response

async def get_single_response(prompt, temperature = 1, max_tokens = 600):
    response = clientopenai.chat.completions.create(
        model="gpt-4o",
        messages=prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    response = response.choices[0].message.content
    return response

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

async def is_image(attachment):
    try:
        if attachment.content_type.startswith("image"):
            image = attachment.url or attachment.proxy_url
            if image:
                return True
            else:
               return False
        else:
           return False
    except Exception as e:
       print(e)
       return False
    
async def parse_link(attachment):
    if await is_image(attachment):
        image = attachment.url or attachment.proxy_url
    return image