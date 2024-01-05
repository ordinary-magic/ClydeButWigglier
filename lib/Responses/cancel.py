import random
from .response import ResponseInterface
from lib.discord_helpers import get_history

class Cancel(ResponseInterface):
  callsign = 'cancel'
  blurb = 'find a problematic comment the user mades'
    
  # Handle the message as requestesd
  async def respond_with_context(self, text, request, channel):
    return await cancel_user(request, channel, lambda x: not 'http' in x)

class BadPost(ResponseInterface):
  callsign = 'badpost'
    
  # Handle the message as requestesd
  async def respond_with_context(self, text, request, channel):
    return await cancel_user(request, channel)
    
# Cacnel user by finding incriminating messages
async def cancel_user(request, channel, filter = lambda _: True):
  if (channel.id != request.channel.id):
    return "This function doesnt work across threads. :shrug:", request

  if len(request.mentions) == 1:
    #if self.is_me(request.mentions[0]):
    #  await self.post("I'm un-cancelable :^)", request)
    #else:
    target = request.mentions[0].id
    evidence = await find_evidence(request.channel, target, filter)
    if evidence:
      return 'Yikes, <@{}>'.format(target), evidence
    else:
      return "<@{}> is pure and wonderful and can do no wrong.".format(target), request
      
      
# Find a message to cancel a user over
async def find_evidence(channel, target, filter, length=20):
  for sus in reversed(await get_history(channel, limit=random.randint(500, 2000))):
    if sus.author.id == target:
      if filter(sus.content):
        if len(sus.content) > length:
          return sus