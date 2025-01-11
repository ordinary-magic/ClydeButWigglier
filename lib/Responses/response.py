from datetime import datetime, timedelta

class ResponseInterface:
  callsign = '' # The flag to register this response for

  blurb = '' # help text blurb to describe the response
  
  # Reference to a method used to run a call in in a new thread
  run_thread = None # async def run_thread(func, *args) -> result
  
  # Reference to a method used to determine if a user is the bot
  is_me = None # # def is_me(id) -> boolean
  
  # Data required by rate limiting of the responses
  cooldown = timedelta(-20) # Default Cooldown is negative in case of race conditions
  last_use = datetime.min # Last use of the response
  manual_timer = False # If True, responses will handle their own timers (check is skipped)
  
  # Generate a static response
  async def respond(self) -> str:
    pass
  
  # Generate a response to the text of a message
  async def respond_to_text(self, text: str) -> str: 
    return await self.respond()
   
  # Respond to the text and context of a message
  async def respond_to_message(self, text: str, request: object) -> str:
    return await self.respond_to_text(text)
   
  # Respond with a custom reply context
  # text: the formatted text of the message
  # request: the message object that triggered this response
  # channel: the channel/thread the response should reply to
  # returns: a tuple of (response_text, message_to_reply_to)
  async def respond_with_context(self, text: str, request: object, channel: object) -> (str, object):
    return await self.respond_to_message(text, request), request

  # Entry point into the class. Will check the cooldown first, then call the response chain
  # Will Return (Message Text, Optional Message to Reply To, Extra kwargs for post command)
  async def get_response(self, text, request, channel):
    if self.manual_timer or self.check_timer():
      return await self.respond_with_context(text, request, channel)
    else:
      return ['!{} is on cooldown ({}s left)'.format(
        self.callsign, self.get_cooldown_time()), request]
    
  # Check if the cooldown timer has elapsed, updating it on success
  def check_timer(self):
    if datetime.now() - self.cooldown > self.last_use:
      self.last_use = datetime.now()
      return True
    else: return False
    
  # Get the remaining cooldown time in seconds
  def get_cooldown_time(self):
    return ((self.cooldown + self.last_use) - datetime.now()).seconds
  
  # Get the detailed help text of a response
  def get_help(self) -> str:
    return "!{} will {}.".format(self.callsign, self.blurb)
    