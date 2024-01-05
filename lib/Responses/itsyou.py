import random
from .response import ResponseInterface
from lib.discord_helpers import get_channel_users, get_reply_context
from lib.giphy import get_random_gif

# WaterPost without the special users
class ItsYou(ResponseInterface):
  callsign = 'itsyou'
  blurb = 'bot will post a random gif that reminds it of a user'
  
  # Respond to the request
  async def respond_with_context(self, text, request, channel):
    # Check if we have a target
    if len(request.mentions) == 1:
      target = request.mentions[0].id
    elif len(request.mentions) > 1:
      target = random.choice(request.mentions).id
    else:
      target = random.choice(get_channel_users(request.channel)).id

    # Determine the topic (usually a cat)
    topic = random.choice(['cat', 'bunny', random.choice(['dog', 'animal', ''])])

    # Post the response
    try:
      await channel.send(content=await  get_random_gif(topic))
      await channel.send("<@{}>, it's you!".format(target))
    except Exception as e:
      return str(e), request
    
    # All Posting is handled internally.
    return None, None