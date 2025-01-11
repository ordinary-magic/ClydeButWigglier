import re
import base64
from io import BytesIO
from openai import AsyncOpenAI
from lib import gptprompts
from .discord_helpers import get_username, strip_flags, get_attached_images, has_images

# Number of tokens allowed per model
DEFAULT_TOKENS = 2048 # Default Value
MAX_TOKENS = {} # Specific Overridees

GPT3 = 'gpt-4o-mini'
GPT4 = 'gpt-4o'
GPT4_VISION = GPT4 # updated GPT4 models have built-in visual analysis
IMAGES = "dall-e-3"

# Check if we've initialized the openai api yet,
#   And get the secret key from local file if not
token = None
def get_client():
  global token
  if not token:
    with open("keys/openai_apikey.txt", "r") as tokenfile:
      token = tokenfile.read()
  return AsyncOpenAI(api_key=token)

# Get a response for a set prompt
async def get_response_to_chat(messages, model=GPT4):
  try:
    return (await get_client().chat.completions.create(
        model = model,
        messages = messages,
        max_tokens = MAX_TOKENS.get(model, DEFAULT_TOKENS),
        temperature=0.90,
      )).choices[0].message.content.strip()
  except Exception as e:
    return str(e)
  
# Get a response for a set prompt
async def get_single_response(prompt, model=GPT3):
  try:
    return (await get_client().completions.create(
        model=model,
        prompt = prompt,
        max_tokens = MAX_TOKENS.get(model, DEFAULT_TOKENS),
        temperature=0.90,
      )).choices[0].text.strip()
  except Exception as e:
    return str(e)

# Generate an image for the requested prompt
#   Will return (image, title) to post.
#   If an error is encountered, image will be None,
#     and the title will be an error message instead
async def get_image_generation(prompt):
  try:
    image_str = (await get_client().images.generate(
        model=IMAGES,
        prompt=prompt,
        size="1024x1024",
        quality="hd",
        n=1,
        response_format='b64_json'
      )).data[0].b64_json
    image = BytesIO(base64.b64decode(image_str.encode()))
    return image, f'"{prompt}"'

  except Exception as e:
    return None, str(e)

# Format a list of discord messaegs in openai's preferred format
def format_message_log(messages, is_me, visual):
  return [convert_to_openai_format(x, is_me, visual) for x in messages]
  
# Convert a discord message to the openai completion format
# message - the message to format
# is_me - a predicate to check if a message was sent by the bot user
# visual - boolen true/false if image embeds are allowed 
def convert_to_openai_format(message, is_me, visual):
  # The bot's role is "assistant", everything else is user. Flag message appropriatley
  role = "user"
  if is_me(message.author) and not visual:
    role = "assistant"
  name = gpt_name(get_username(message.author))

  # Content is either the text content of the message, or
  #   a formatted dictionary of text and image attachments
  content = strip_flags(message.content)
  images = get_attached_images(message) if visual else []
  if images:
    content = [{'type':'text', 'text':content}]
    content += [{'type':'image_url', "image_url": {"url": url}} for url in images]

  # Return the composed dictionary
  return {"role": role, "content": content, "name": name}

# Get a chatgpt response to a series of discord messages.
# messages - a list of discord messages comprising the chat context
# is_me - predicate to identify if a message was sent by the bot user
# model - the openai model to use when responding
# visual - true/false if model needs to respond to images
async def respond_to_messages(messages, is_me, model, visual = False):
  task = gptprompts.get_prompt(messages[0].guild.id, messages[0].channel.id)
  frame = {"role": "system", "content": task}
  prompt = [frame] + format_message_log(messages, is_me, visual)
  return await get_response_to_chat(prompt, model)

# They keep killing my models :(
#  Use the cheap chat completion model with no prompt instead
# reply_to is an optional message to reply to
async def wiggly_chat_response(request, is_me, reply_to, visual):
  # Add context in "s if needed
  messages = ([reply_to] if reply_to else []) + [request]
  model = GPT4_VISION if visual else GPT3
  prompt = format_message_log(messages, is_me, visual)
  return await get_response_to_chat(prompt, model) or ":confused:"

# Get a more wiggly response to a single message, including an optional quote
#  Note: Uses the davinci-003 model, which is significantly less gatekept
async def wiggly_response(prompt, reply_to=None):
  # Add context in "s if needed
  if(reply_to):
    prompt = '"{}"\n{}'.format(reply_to.content, prompt)
  return await get_single_response(prompt) or ":confused:"

# Get a chatgpt response to a series of discord messages.
# messages - A list of the discord messages to which we are responding.
# prompt - the custom prompt to use in the response
# is_me - predicate to identify if a message was sent by the bot user
# model - the openai model to use when responding
async def respond_to_messages_with_customized_prompt(messages, prompt, is_me, model=GPT4):
  visual = any([has_images(m) for m in messages])
  frame = {"role": "system", "content": prompt}
  query = [frame] + format_message_log(messages, is_me, visual)
  return await get_response_to_chat(query, model)

# Convert all openai friendly name's _id_ to discord id's <@id> in the string
def name_to_id(text):
  return re.sub(r'_(\d+)_', r'<@\1>', text)
  
# Convert all discord id's <@id> to openai friendly name's _id_ in the string
def id_to_name(text):
  return re.sub(r'<@(\d+)>', r'_\1_', text)

# Get a gpt friendly string
def gpt_name(text):
  return re.sub(r'[^a-zA-Z0-9_-]', '', text) or 'a'