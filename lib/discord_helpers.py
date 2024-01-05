# Pile of various helper methods to do discord api things
from lib.userdata import get_name_and_pronouns
import re
from discord import File as dfile

# Get the chat history of a specific channel
async def get_history(channel, **kwargs):
  return [x async for x in channel.history(**kwargs)]

# Turn a partial reference embedded within the input message
#   into a fully resolved message and return it (or None, of not found)
async def resolve_reference(message):
  reference = message.reference
  if (reference):
    try:
      channel = message.channel
      return await channel.fetch_message(reference.message_id)
    except:
      print("couldnt resolve reference")
  return None
  
# Get a string username for a given user
def get_username(user):
  return user.nick or user.name
  
 # Grammatical join of a list (eg. a, b, and c)  
def grammar_join(list):
  return ", ".join(list[:-2] + [" and ".join(list[-2:])])
  
# Strip any leading mentions from the input text
def strip_mentions(text):
  while text.startswith('<@'):
    text = (text.split(None, 1) + [''])[1]
  return text.strip()
  
# Strip any leading flags from the input text
def strip_flags(text):
  while text.startswith('!'):
    text = (text.split(None, 1) + [''])[1]
  return text.strip()

# Get the users who can see a particular message
# Excluding all bots
def get_channel_users(channel):
  return [user for user in channel.members if (not user.bot)]

# Get a comma seperated string of all users in the channel
#   Will include pronouns whenever possible
# eg. "Alice (she/her), Bob (he/him), Clive (They/Them), Dan"
# Includes the bot if specified
def get_channel_users_string(server, channel, bot_user):
  names = []
  for user in get_channel_users(channel):
    uinfo = get_name_and_pronouns(server.id, user.id) # Get stored user data
    
    #Try to use a user's preset name, and fall to their display name
    name = uinfo[0] if uinfo[0] else get_username(user)
    
    # check if the user specified pronouns
    if (uinfo[1]): 
      name += f' ({uinfo[1]})'
    names += [name]

  # Add the bot to the list if requested
  if bot_user:
    names += [bot_user.name + ' (it/its)']

  # And return the list of names
  return grammar_join(names)

# Pick a name for a new thread, using the author name and message text
# Threads require a name with 1 and 100 characters, but do not have to be unique
def pick_thread_name(message, text):
  text = replace_at_with_text(message.channel, text)
  name = f'{get_username(message.author)}\'s Thread: {text}'
  
  if len(name) > 97:
    name = name[:97].strip() + '...'
  return name

# Replace all <@1234> mentions with @username in the input string
def replace_at_with_text(channel, text):
  ids = [int(x) for x in re.findall('<@(\d+)>', text)]
  users = [next((user for user in channel.members if user.id == id), None) for id in ids]
  names = [get_username(user) if user else '???' for user in users]
  
  for id, name in zip(ids, names):
    text = re.sub(f'<@{id}>', f'@{name}', text)
  return text

# Get the correct posting context across threads
# (Reply to the original post, unless we're in a thread)
def get_reply_context(request, channel):
  #  Check if we're in a thread
  if channel.id == request.channel.id:
    return request.reply
  else:
    return channel.send
  
# Convert a list of images into the format used in discord posts
def package_discord_images(images):
  return [dfile(image, 'image.jpg') for image in images]

# Get an array of urls for all images attached to the input message
def get_attached_images(message):
  images = []
  for attachment in message.attachments:
    if attachment.content_type.split('/')[0] == 'image':
      images += [attachment.url]
  return images

# True/Flase indicating if the message has any attached images
def has_images(message):
  for attachment in message.attachments:
    if attachment.content_type.split('/')[0] == 'image':
      return True
  return False