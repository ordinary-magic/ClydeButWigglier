# Library Imports
import discord
import asyncio
import concurrent.futures
from textwrap import wrap
import random

# Local Imports
from lib.discord_helpers import *
from lib.Responses import *
from lib.uwuify import uwu, UwuifyFlag as fwag

class RemiliaClakeBot(discord.Client):
  # Function executed when bot connects
  async def on_ready(self):
    # Register the response pool
    self.responses = self.init_responses()
  
    # Setup useful resources
    self.thread_pool = concurrent.futures.ThreadPoolExecutor()
    self._post_lock = asyncio.Lock() # Mutex lock to stop replies from interrupting eachother
    
    # Alert the admin (me) we're ready to start
    print('\nConnected!')
    print('Username: {0.name}\nID: {0.id}'.format(self.user))
    
  # Check if the user is me
  def is_me(self, user):
    return user.id == self.user.id

  # Message event handler (will dispatch new thread)
  async def on_message(self, message):
    if self.is_me(message.author):
      return
    
    # Extract relevant info from the message before we modify it
    flags, text = self.extract_flags(message.content)
    mentions = message.mentions
    channel = message.channel

    # Preprocess text
    text = self.preprocess_text(text, message)

    # Start a new thread if requested and we're not already in one.
    new_thread = 'thread' in flags and channel.type is discord.ChannelType.text
    if new_thread:
      # Create a new thread and reply to this message in there instead
      channel = await message.create_thread(name=pick_thread_name(message, text))

    replies = [] # Text to post at the end of this (only sometimes tho)

    # Check if we were mentioned directly (takes priority over other stuff)
    if any(map(self.is_me, mentions)):  
      # Manually call the secret chatgpt response handler
      replies.append(await self.responses['_gpt'].get_response(text, message, channel))
    
    # Otherwise, check for any commands
    else:
      for flag in set(flags) & set(self.responses.keys()):
        replies.append(await self.responses[flag].get_response(text, message, channel))

    # reply to all relevant messages
    for reply in replies:
      if reply[0]: # Check No-Post Condition
        text = self.apply_text_modifiers(reply[0], flags)
        post_kwargs = self.get_extra_post_kwargs(flags)

        # Check if we're supposed to reply to a message
        # (Dont Reply to thread starting messages, discord doesnt like it)
        if not reply[1] or new_thread:
          await self.post(text, channel, post_kwargs, is_reply=False)
        else:
          await self.post(text, reply[1], post_kwargs)
  
  # Extract any flags from the text
  # (flags are extra commands that start with ! and are at the start of the message)
  def extract_flags(self, text):
    flags = []
    while text.startswith('!'):
      [newflag, text] = (text.split(None, 1) + [''])[:2]
      flags.append(newflag.lower()[1:])
    return flags, text
    
  # Collect arguments to pass to the discord messagable.Post api endpoint
  def get_extra_post_kwargs(self, flags):
    post_kwargs = {}
    if 'tts' in flags:
      post_kwargs['tts'] = True
    return post_kwargs
  
  # Do any preprocessing of the message here
  # e.g. replace $users with a list of the server's users, etc.
  def preprocess_text(self, text, request):
    if '$users' in text:
      user_string = get_channel_users_string(request.guild, request.channel, self.user)
      text = text.replace("$users", user_string)
    return text
  
  # Apply Text Modifiers to the input string based on the requested flags
  def apply_text_modifiers(self, text, flags):
    if 'uwu' in flags:
      text = uwu(text, flags=fwag.SMILEY | fwag.YU | fwag.STUTTER)
    if 'yell' in flags:
      text = text.upper()
    
    # Check if response is shiny (should be last for emote formatting)
    if random.randrange(8191) == 1: 
      text = ':sparkles:{}:sparkles:'.format(text)
      
    return text

  # Post a message with input content to the channel in the provided message context
  async def post(self, content, context, post_kwargs, is_reply=True, start_thread=False):    
    async with self._post_lock: # Only one message at a time
      try:
        # Break up messages longer than the max character limit
        chunks = wrap(content, 2000, replace_whitespace=False, drop_whitespace=False)
        if(is_reply):
          await context.reply(content=chunks[0], **post_kwargs)
          context = context.channel # Set the channel as the new context for multi-part-messages
        else:
          await context.send(content=chunks[0], **post_kwargs)

        # Queue up any additonal message chunks
        if len(chunks) > 1:
          for part in chunks[1:]:
            await context.send(content=part, **post_kwargs)
      except Exception as e:
        print(e)

  # helper funciton to run a function in a thread
  async def run_thread(self, func, *args):
    return await self.loop.run_in_executor(self.thread_pool, func, *args)

  # Dynamically collect and instantiate the command/response dictionary
  def init_responses(self):
    responses = {}
    for cls in ResponseInterface.__subclasses__():
      inst = cls()
      inst.run_thread = self.run_thread
      inst.is_me = self.is_me
      responses[inst.callsign] = inst
      print("'{}' registered to '{}'".format(cls.__name__, inst.callsign))

    # Make the help response aware of the avaliable options
    responses['help'].responses = responses
    
    return responses

# Function to get the bot authentication token from a file
def get_token():
  with open("keys/discord_token.txt", "r") as token:
    return token.read()

# Get the intents the bot needs to function
def get_intents():
  intents = discord.Intents.default()
  intents.message_content = True
  intents.members = True
  return intents

# Run the server on startup
client = RemiliaClakeBot(intents=get_intents())
client.run(get_token())