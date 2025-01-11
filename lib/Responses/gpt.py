from .response import ResponseInterface
from lib import chatgpt
from lib import gptprompts
from lib.discord_helpers import *

class GptResponse(ResponseInterface):
  callsign = '_gpt' # Keep this sorta hidden
  
  # Generate a reply to a single message using davinici (without guardrails)
  async def respond_to_message(self, text, request):
    # Respond to the request
    quote = await resolve_reference(request)
    visual = has_images(request) or (quote and has_images(quote))
    return await chatgpt.wiggly_chat_response(request, self.is_me, quote, visual)
    
class GptCompletion(ResponseInterface):
  callsign = 'ai'
  blurb = 'get GPT-3.5 to respond to the chat'
    
  # Generate a chat completion reply to the exisitng chat log
  async def respond_to_message(self, text, request):
    request.content = text
    context = gptprompts.get_context(request.guild.id, request.channel.id)
    messages = [request] + await get_history(request.channel, limit=context, before=request)
    messages.reverse()
    return await chatgpt.respond_to_messages(messages, self.is_me, chatgpt.GPT3)

class Gpt4Completion(ResponseInterface):
  callsign = 'ai4'
  blurb = 'get GPT-4 to respond to the chat'

  # Generate a chat completion reply to the exisitng chat log
  async def respond_to_message(self, text, request):
    request.content = text
    context = gptprompts.get_context(request.guild.id, request.channel.id)
    messages = [request] + await get_history(request.channel, limit=context, before=request)
    messages.reverse()
    visual = any([has_images(m) for m in messages])
    model =  chatgpt.GPT4_VISION if visual else chatgpt.GPT4
    return await chatgpt.respond_to_messages(messages, self.is_me, model, visual)
    
class ChangePrompt(ResponseInterface):
  callsign = 'prompt' # Set the current prompt
  blurb = 'check or change the current GPT prompt'
  
  # Generate a response to a message
  async def respond_with_context(self, text, message, channel): 
    return gptprompts.set_prompt(text, message.guild.id, channel.id), message
  
  # Get the help text from the module
  def get_help(self):
    return 'To see the current prompt, use "!prompt" with no arguments' +\
           'To use a preset prompt, use "!prompt <number>"' +\
           'To set a custom prompt, use "!prompt custom <text>"'
   
class ChangeContext(ResponseInterface):
  callsign = 'context' # Set the current context
  blurb = 'check or change the ammount of messages !ai commands see'
  
  # Generate a response to a message
  async def respond_with_context(self, text, message, channel): 
    return gptprompts.set_context(text, message.guild.id, channel.id), message
  
  # Get the help text from the module
  def get_help(self):
    return 'Context controls how many messages the !ai commands have accesss to.\n' +\
           'To see the current context amount, use "!context" with no arguments\n' +\
           'To overwrite it, use "!context <value>"\n' +\
           '<value> must be whole, non-negative number.'

class ListPrompts(ResponseInterface):
  callsign = 'prompts' # List all avaliable prompts
  blurb = 'see all avaliable preconfigured GPT prompts'
  
  async def respond(self):
    return gptprompts.list_prompts()
    
# Class used for 'pre-baked' gpt prompts    
class GptInterface():
  # The customized prompt used in the response (should be overridden)
  # Note that, if you wish to address the user(s) by name, you can use {0} within the prompt or reasoning
  prompt = ''

  # text_reasoning is appended to the prompt if the user gave a string of text explaining the reasoning.
  #  eg. "!insult @user1 for being rude" would prompt gpt with "Insult user1 for being rude."
  # Use {1} to reference this text reason if you override this.
  text_reasoning = '{1}'

  # reasoned_prompt is appended to the prompt if the user gave a quote in order to prompt gpt to address it.
  #  eg. replying to user1's message with "!insult" would prompt gpt with "insult user1 for the following message:", followed by the message
  quote_reasoning = 'for the following message:'

  # no_reasoning is appended to the prompt if the user did not give any reason for the invocation.
  #  eg. posting "!insult @user1" with no extra text.
  no_reasoning = ''

  # Text to return instead of '' if the model doesnt generate anything
  no_response = ':confused:'

  # Text to return if the user fails to provide a valid target.
  bad_request = 'Please provide a valid target.'

  # True/False does this response use the channel's current gpt prompt personality
  has_personality = False 
    
  # Common method to handle setup for personalized responses (eg insult/praise)
  # Implementing classes should call this from their respond_to_message methods to get the response
  # text - the text provided by the response method.
  # request - the discord message that triggered this response
  async def get_customized_response(self, text, request):
    # Either find the target or target the user for failing to provide one
    reference = await resolve_reference(request)
    is_me = lambda _: False # Single command responses like this can never target the bot.

    if (reference):
      # Replying to a message
      name = get_username(reference.author)
      prompt = (self.prompt + ' ' + self.quote_reasoning).format(name)
      messages = [reference]

    else:
      # Inline reasoning
      reason = strip_mentions(text)
      names = set([get_username(x) for x in request.mentions if not is_me(x)])
      
      if not names: # User didnt give anybody to target, use the fallback message.
        return self.bad_request

      name = grammar_join(list(names)) # need to go set->list to remove duplicates
      messages = []

      if (reason): # Text reason was provided
        prompt = (self.prompt + ' ' + self.text_reasoning).format(name, reason)

      else: # Text reason was not provided
        prompt = (self.prompt + ' ' + self.no_reasoning).format(name)

      # If the response is supposed to use the channel's personality, add it to the prompt.
      if self.has_personality:
        personality = gptprompts.get_prompt(request.guild.id, request.channel.id)
        prompt = personality + '\n\n' + prompt

    # Get the respones
    response = await chatgpt.respond_to_messages_with_customized_prompt(messages, prompt, is_me)
    return response or self.no_response

class Insult(ResponseInterface, GptInterface):
  callsign = 'insult'
  blurb = 'generate a message insulting a user'
  prompt = 'Pretend to agressivley insult and mockingly deride "{0}"'
  quote_reasoning = 'for foolishly posting the following message:'
  no_reasoning = "in a silly way, for a made-up silly reason of your choosing."
  bad_request = 'god you suck'
  no_response = ':rage:'

  async def respond_to_message(self, text, request):
    return await self.get_customized_response(text, request)

class Praise(ResponseInterface, GptInterface):
  callsign = 'praise'
  blurb = 'generate a message praising a user'
  prompt = 'Praise and dote on "{0}" and tell them they did a good job'
  bad_request = 'you tried your best, and thats what matters!'
  no_response = ':heart:'

  async def respond_to_message(self, text, request):
    return await self.get_customized_response(text, request)

class Apologize(ResponseInterface, GptInterface):
  callsign = 'sorry'
  blurb = 'generate an apology on behalf of a message'
  prompt = 'Apologize profusely on behalf of "{0}"'
  bad_request = 'im truly sorry for this'
  no_response = ':pensive:'

  async def respond_to_message(self, text, request):
    return await self.get_customized_response(text, request)

class Monologue(ResponseInterface, GptInterface):
  callsign = 'monologue'
  blurb = 'flaunt your imminent victory'
  prompt = 'Flaunt your imminent victory over "{0}" with a wry and flamboyant monologue. Play up your character\'s special traits, or invent some if none ar provided. Your monologue should be no more than 100 words long, and should end with a short, 1-5 word phrase declaring your monment of victory, such as "farewell", the name of your final special attack, or some other pithy summarization of your opponent ({0}\'s) failures.'
  text_reasoning = 'You are monologuing {1}'
  quote_reasoning = 'The following message contains their last pathetic words to you:'
  bad_request = "You're even worth monologuing at."
  no_response = 'hmph'
  has_personality = True

  async def respond_to_message(self, text, request):
    return await self.get_customized_response(text, request)

# Get a DALLE image for your prompt
class GPTImageGeneration(ResponseInterface):
  callsign = 'aiimage'
  blurb = 'use DALLE3 to generate an image for your prompt'
    
  # Respond to the message
  async def respond_with_context(self, text, request, channel):
    post = get_reply_context(request, channel)
    image, reply = await chatgpt.get_image_generation(text)
    if image:
      images = package_discord_images([image])
      await post(content=reply, files=images)
    else:
      await post(content=reply)

    # All Posting is handled internally.
    return None, None