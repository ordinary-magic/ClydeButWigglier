from .response import ResponseInterface
import random
import time

# Time Command (the OG)
class Time(ResponseInterface):
  callsign = 'time'
  blurb = 'get the current time'
  
  async def respond_with_context(self, text, request, channel):
    # Target the mentioned user, or the author as appropriate
    target = request.author.id
    if len(request.mentions) == 1:
      target = request.mentions[0].id

    text = f'<@{target}>, your current time is <t:{int(time.time())}:t>. Yay!'
    return text, None # None means it wont reply (legacy inclusion)

# Echo command (for debugging)
class Echo(ResponseInterface):
  callsign = 'echo'

  async def respond_to_text(self, text):
    return text

# Ravioli command (courtesy of Billie)    
class Ravioli(ResponseInterface):
  callsign = 'ravioli'
  
  async def respond(self):
    return 'i feel down the stairs and ravioli on me'
  
# Magic 8-ball command
class EightBall(ResponseInterface):
  callsign = '8ball'
  blurb = 'get deep wisdom in response to your yes or no question'

  # the 20 canonical responses (according to wikipedia)
  responses_canon_yes =   ['It is certain.', 'It is decidedly so.', 'Without a doubt.',
                          'Yes, definitely.', 'You may rely on it.', 'As I see it, yes.',
                          'Most likely.', 'Outlook good.', 'Yes.' , 'Signs point to yes.']
  responses_canon_maybe = ['Reply hazy, try again.', 'Ask again later.', 'Better not tell you now.',
                          'Cannot predict now.', 'Concentrate and ask again.']
  responses_canon_no =    ['Don\'t count on it.', 'My reply is no.', 'My sources say no.', 
                           'Outlook not so good.', 'Very doubtful.']
  # some wiggly options
  responses_wiggly =      [ '¯\_(ツ)_/¯', 'Ask pamitha', 'go away', 'meowwww :3']
  

  async def respond(self):
    roll = random.random()
    if roll < 0.25:
      return random.choice(self.responses_canon_maybe)
    elif roll < 0.6:
      return random.choice(self.responses_canon_yes)
    elif roll < 0.95:
      return random.choice(self.responses_canon_no)
    else:
      return random.choice(self.responses_wiggly)
    
# Scared command (bc its cute)
class Scared(ResponseInterface):
  callsign = 'aaa'
  
  async def respond(self):
    return 'a' * 2001

# I Want To Remove This Stupid Ass Command
class HighCheck(ResponseInterface):
  callsign = 'high'
  adjetives = ["strung-out", "intoxicated", "ripped", "tipsy", "wasted", "baked", "bombed", "buzzed", "doped", "drugged", "drunk", "fried", "inebriated", "loaded", "plastered", "sloshed", "smashed", "stewed", "tanked", "totaled", "tripping", "boozed up", "on a trip", "spaced out", "high"]    

  # Randomly determine how high a user is
  async def respond_to_message(self, text, request):
    if len(request.mentions) == 1:
      target = request.mentions[0].id
      type = random.choice(self.adjetives)
      percentage = random.randint(0,1000)/10.0
      return '<@{}> is {}% {}'.format(target, percentage, type)
    else:
      return None
