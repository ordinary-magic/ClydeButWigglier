from .response import ResponseInterface
  
# Response to provide help using the bot and tracking its many commands
class Help(ResponseInterface):
  callsign = 'help'
  blurb = 'get help with using the bot'

  responses = {} # list of response classes the server is aware of
  
  # Get help text for a requested subset of commands, or a list of commands
  async def respond_to_text(self, text):
    # determine if the user wants specific or general help
    shortlist = self.get_multiple_commands_help(text)
    if (shortlist): return shortlist
    else: return get_command_list(self.responses)
  
  # Get the detailed help text for all responses requested in the input text
  def get_multiple_commands_help(self, text):
    callsigns = text.split(' ')
    return "\n\n".join(filter(None, map(self.get_single_command_help, callsigns)))

  # Get the detailed help text for a specific callsign
  def get_single_command_help(self, callsign):
    if callsign in self.responses.keys():
      return self.responses[callsign].get_help()
    else: return None

# Get a formatted list of commands in the server
def get_command_list(responses):
  text = 'Sure! here is a list of commands:'
  
  # List all comands with a valid help blurb
  for response in filter(lambda x: x.blurb, responses.values()):
    text += "\n* {}: {}".format(response.callsign, response.blurb) 

  return text + get_non_response_commands()

# Get the help text of commands that aren't responses
def get_non_response_commands():
  return '\n* !thread: respond in a new thread' +\
         '\n* !tts: say the response aloud' +\
         '\n* !uwu: uwuifwy the wesponse' +\
         '\n* !yell: RESPOND VERY LOUDLY'