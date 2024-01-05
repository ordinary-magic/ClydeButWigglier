from datetime import timedelta
from .response import ResponseInterface
from lib.spongebobcase import to_spongecase
from lib.discord_helpers import resolve_reference
  
# Mock Interface in its own file so I can turn it off easier
class Mock(ResponseInterface):
  callsign = 'mock'
  blurb = 'mock a user (long cooldown)'
  cooldown = timedelta(hours=2)
  
  # Check conditions then respond by mocking a user with spongebob case
  async def respond_with_context(self, text, request, channel):
    # Check if there was a reply to determine who we are mocking
    reference = await resolve_reference(request)
    if(reference):
      return to_spongecase(reference.content), reference
    else:
      return to_spongecase(text), request