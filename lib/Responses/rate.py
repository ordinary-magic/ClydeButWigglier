from .response import ResponseInterface
from lib import postrater
from lib.discord_helpers import resolve_reference, get_history


class Rate(ResponseInterface):
  callsign = 'rate'
  blurb = 'rate the quality of a post'

  def __init__(self):
    self.rater = postrater.PostRater()
  
  # Respond with a custom reply context
  async def respond_with_context(self, text, request, channel):
    target = await resolve_reference(request)
    if(target):
      text = target.content
      # removed !self check bc it was hard 2 do, and is handled by top lvl response filtering
      history = await self.get_ratable_chat_history(request.channel, before=target.created_at)
      
      result = ":confused:"      
      if 'detail' in text.lower():
        result = await self.run_thread(self.rater.get_detailed_rating, text, history)
      else:
        result = await self.run_thread(self.rater.get_rating, text, history)
        
      return result, target
    
    else: # return an error condition
      return None, None

  # Get the text contents of the last n chat messages in the channel
  async def get_ratable_chat_history(self, channel, before, n=10):
    history = await get_history(channel, limit=2*n, before=before)
    # Its probably more correct to include the bot in the history, esp since it can
    #   do large, on topic responses. (prob higher quality than the users, tbh)
    #notme = filter(lambda x: not self.is_me(x.author), history)
    return list(map(lambda x: x.content, history))[:n]