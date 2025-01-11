# Module to manage gpt prompt access
import lib.channeldata as db

DEFAULT_CONTEXT = 5

# Get the saved prompt or the default one
def get_prompt(server: int, channel: int):
  prompt = db.get_prompt(server, channel)
  return prompt or pick_prompt('1')

# Get the saved context amount, or the default value
def get_context(server: int, channel: int):
  context = db.get_context(server, channel)
  if context is None: # 0 is valid but false
    return DEFAULT_CONTEXT
  return context

# Read the preset prompts out of the file
def get_prompts():
  with open("data/prompts.txt", 'r') as prompt_data:
    next(prompt_data) # ignore the descriptive comment line
    return [line.strip().split('::') for line in prompt_data]

# Set the prompt to one of the pre-existing ones
def pick_prompt(selection: str):
  newprompt = None
  if selection.isdigit():
    try: newprompt = get_prompts()[int(selection) - 1][1]
    except: print("could not set prompt to {}".format(selection))
  else:
    for prompt in get_prompts():
      if selection == prompt[0]:
        newprompt = prompt[1]
  return newprompt
  
# Set the prompt from a user's message
def set_prompt(message_text: str, server: int, channel: int):
  # Check if the user wants the current prompt
  if len(message_text.strip()) == 0:
    return f"The Current Prompt Is:\n> {get_prompt(server, channel)}"
    
  newprompt = None

  # Check for custom prompts
  if message_text.split(' ')[0].lower() == 'custom':
    newprompt = message_text.split(' ', 1)[1]
  
  else: # Use a premade prompt
    newprompt = pick_prompt(message_text)
    
  if newprompt:
    update_db(server, channel, prompt=newprompt)
    return "Prompt set to:\n> {}".format(newprompt)
  else:
    return '"{}" didnt match any of the existing prompt names.\n\nPlease pick a number or name from the list, or use !prompt custom <prompt> to set your own.'.format(message_text)

# Set the context as requested in the supplied message
def set_context(message_text: str, server: int, channel: int):
  if not message_text: # empty message, get the context
    return f'!ai commands will use {get_context(server, channel)} lines of context'
  elif message_text.isdigit() and int(message_text) >= 0:
    update_db(server, channel, context=int(message_text))
    return f'Context set to {message_text}.'
  else:
    return f'Could not set context amount to "{message_text}"'

# Push an update to the db. Updates both in case of newly added rows, 
#   but uses existing values or defaults for non-specified fields
def update_db(server: int, channel: int, prompt : str = None, context : int = -1):
  db.set_context(server, channel, context if context > -1 else get_context(server, channel))
  db.set_prompt(server, channel, prompt if prompt else get_prompt(server, channel))

# List the default prompts
def list_prompts():
  response = "The Default Prompts Are:"
  
  index = 0
  for prompt in get_prompts():
    index += 1
    response += "\n{}) {}\n> {}".format(index, prompt[0], prompt[1])
    
  return response