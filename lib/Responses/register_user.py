from .response import ResponseInterface
from lib import serverdata as db

def is_pam_name(name: str) -> bool:
    # rudimentary check to see if someone is trying to be pamitha
    found = False
    for fix in ['pam', 'tha', 'kay', 'yla']:
        if fix in name:
            found = True
            break
    return found

def update_pronouns(server: int, id: int, target: str, delete: bool = False) -> str:
    p_string = db.get_name_and_pronouns(server, id)[1]
    if (p_string):
        p_list = p_string.split(', ') # pronouns are comma seperated list
    else:
        p_list = []
    
    if delete:
        if len(p_list) == 0:
            return 'You don\'t have any pronouns.'
        if target in p_list:
            p_list.remove(target)
            if len(p_list) > 0:
                p_string = ', '.join(p_list)
                db.set_pronouns(server, id, p_string)
                return f'Your updated pronouns are: {p_string}'
            else:
                db.set_pronouns(server, id, '')
                return f'Your pronouns have been deleted.'
        else:
            return f'You don\'t have those pronouns. Current pronouns are: {", ".join(p_string)}'
    else:
        if target in p_list:
            return 'You already have those pronouns.'
        else:
            p_list.append(target)
            p_string = ', '.join(p_list)
            db.set_pronouns(server, id, p_string)
            return f'Okay, I\'ll remember your pronouns: {p_string}'
        
def update_name(server: int, id: int, target: str) -> str:
    if (id != 275787113050406923) and is_pam_name(target.lower()):
        # someone is trying to impersonate pam. we must defend her
        return "I don't think that's really your name..."
    db.set_name(server, id, target)
    return f'Your name has been registered as {target}.'

# Interface for registering your preferred name or pronouns with the bot
class UserRegistration(ResponseInterface):
    callsign = 'register'
    blurb = 'register your preferred name/pronoun for ai responses'

    async def respond_to_message(self, text, message):
        args = text.split(' ')
        server = message.guild.id
    
        if len(args) >= 2:
            if args[0].lower() == 'name':
                return update_name(server, message.author.id, ' '.join(args[1:]))
            elif args[0].lower() == 'pronouns':
                if args[1].lower() == '-a' and len(args) >= 3:
                    return update_pronouns(server, message.author.id, args[2].lower())
                elif args[1].lower() == '-d' and len(args) >= 3:
                    return update_pronouns(server, message.author.id, args[2].lower(), delete=True)
                else: # treat as add
                    return update_pronouns(server, message.author.id, args[1].lower())
                
        # Incorrectly formatted request, refer user to the help text                
        return self.get_help()
  
    # Get the help text for the module
    def get_help(self):
        return f'!{self.callsign} Usage:\n' +\
               f'> "!{self.callsign} name <name>" to set your name.\n' + \
               f'> "!{self.callsign} pronouns -a/-d <pronouns>" to (a)dd or (d)elete pronouns'
  
# Test interface for querying your preferred name or pronouns with the bot
class WhoIsUser(ResponseInterface):
  callsign = 'whois'
  blurb = 'get info about user(s) in the server'
  
  # Inform the user of what they wish to know
  async def respond_to_message(self, text, message):
    args = text.split(' ')
    server = message.guild.id

    if args[0] == '':
        name, pronouns = db.get_name_and_pronouns(server, message.author.id)
        if not name:
            return 'I don\'t know who you are yet! Register your name or pronouns with !register.'
        return f'You are {name}. ' if name else 'You have not registered your name yet. ' + \
            (f'You have the following pronouns: {pronouns}' if pronouns else '')
    elif args[0] == '-l':
        names = ', '.join(db.get_all_names(server))
        return f'Here are all the users who have told me their names: {names}'
    else:
        name = ' '.join(args)
        p = db.get_pronouns_for_name(server, name)
        if len(p) == 0:
            return f'I don\'t know anyone named {name}.'
        elif len(p) == 1:
            if (p[0]):
                return f'The user named {name} uses {p[0]} pronouns.'
            else:
                return f'The user named {name} doesn\'t have any pronouns set.'
        elif len(p) == 2:
            # do not suffer this tomfoolery
            return f'There are multiple people here by the name {name} and they are all ruining my life'
