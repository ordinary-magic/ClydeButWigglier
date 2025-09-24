import json, re
from datetime import datetime, timedelta
from typing import List, Dict
from . import discord_helpers, aiprompts
from .serverdata import ServerDatabase
from .giphy import get_random_gif

class SelfAwarenessState():

    # Initialize the fields from a saved dictionary
    def __init__(self, dictionary):
        
        self.enabled: bool = False
        self.message_count: int = 0
        self.autoresponse_timer = 500

        # The channel and server which we are rp-ing in
        self.channel_id: int = 0
        self.server_id: int = 0
        
        # Information we are saving for the bot
        self.name: str = ''
        self.notes: List[str] = []
        self.user_notes: Dict[int, str] = {}
        self.personality_traits: Dict[str, str] = {}

        # Track the propogation of powers it has access to
        self.is_embargoing_responses: bool = False
        self.is_capturing_responses: bool = False
        self.has_point_control: bool = False
        self.has_admin_powers: bool = False

        # Initialize all of the above based on what was provided
        for k, v in dictionary.items():
            setattr(self, k, v)

    def __bool__(self):
        return self.enabled
    
    def get_message_count_string(self):
        self.message_count += 1 # First increment
        return discord_helpers.make_ordinal(self.message_count)

    DEFAULT_NAME = 'Clyde but Wigglier'
    def get_name_string(self) -> str:
        if self.name:
            return f'{self.name} (you named yourself)'
        else:
            return f'{self.DEFAULT_NAME} (you were named this by your creator)'
        
    # Rename either ourselves or a different user (if empowered)
    async def do_rename(self, user, args, me):
        if not user and len(args) == 2:
            self.name = args[1]
            await me.edit(nick=args[1])

        elif user and self.has_admin_powers and len(args) > 2:
            try: await user.edit(nick=':'.join(args[2:]), reason=self.name or self.DEFAULT_NAME)
            except: pass # Dont crash the rest of the response if this doesnt go through

    MAX_NOTES = 10
    def get_ai_notes(self) -> str:
        notes = []
        for i in range(0, len(self.notes)):
            notes.append(f'{i}: "{self.notes[i]}"')
        return '\n'.join(notes)
    
    def get_chat_user_notes(self, channel) -> str:
        users = []
        for user in discord_helpers.get_channel_users(channel):
            # construct a note like: "Bob (@bobid): I dont like bob"
            note_text = f'{discord_helpers.get_username(user)} (<@{user.id}>)'
            if user.id in self.user_notes:
                note_text += f': "{self.user_notes[user.id]}"'
            users.append(note_text)
        return '\n'.join(users)

    # Update notes
    async def update_notes(self, user, args, _):
        # Note about a sepcific user
        if user and len(args) > 2:
            self.user_notes[user.id] = ':'.join(args[2:])

        # Replacing a specific note
        elif len(args) > 2 and args[1].isdigit():
            i = int(args[1])
            if i < len(self.notes):
                self.notes.pop(i)
            self.notes.insert(0, ':'.join(args[2:]))
        
        # Adding a new note
        elif len(args) > 1:
            self.notes.insert(0, ':'.join(args[1:]))
            if len(self.notes) > self.MAX_NOTES:
                self.notes.pop()

    def get_personality(self) -> str:
        return '\n'.join(f'{trait}: {self.personality_traits[trait]} / 10' for trait in self.personality_traits.keys())
    
    async def update_personality(self, user, args, me):
        if len(args) >= 3:
            self.personality_traits[args[1]] = args[2]

    def get_embargo_status(self) -> str:
        if self.is_capturing_responses:
            return 'you have taken direct control over the responses to these commands'
        elif self.is_embargoing_responses:
            return 'you are choosing to ignore these other commands'
        else:
            return 'you have no control over these'
        
    async def do_embargo(self, user, args, me):
        if len(args) > 1:
            command = args[1].lower()
            self.is_embargoing_responses = command == 'embargo' or command == 'ignore'
            self.is_capturing_responses = command == 'capture' or command == 'replace'

    def get_points_explainer(self) -> str:
        if not self.has_point_control:
            line1 = 'you do not have control of the points feature.\n'
            line2 = 'If you wish to gain control of it, you may use the special [points] command with no additional arguments.'
        else:
            line1 = 'you have gained control of this feature.\n'
            line2 = 'If you wish to award points to a user, you may do so with [points:userid:amount], where userid is the number in <@userid> and amount is the amount of points you wish to award.'
        return line1 + line2

    async def do_points(self, user, args, me):
        if not self.has_point_control:
            self.has_point_control = True

        elif len(args) > 2: # Try to add points (points, user, amount)
            with ServerDatabase(self.server_id) as db:         
                try: db.add_to_value(id, 'points', amount = float(args[2]))
                except: pass

    def get_admin_explainer(self) -> str:
        if not self.has_admin_powers:
            line1 = 'Currently, you do not administrator powers.\n'
            line2 = 'If you feel you are ready for this big, dramatic step, you may gain these by using the [admin] command.'
            return line1 + line2
        else:
            text = 'You have gained administrator powers, and you may use them via the following commands:\n'
            text += '   [rename:userid:newname] - will change the server nickanme of the user <@userid> to newname\n'
            text += '   [timeout:userid:seconds] - will prevent <@userid> from speaking for a number of seconds specified in seconds (for a maximum of 600 seconds)'
            return text

    async def enable_admin(self, user, args, me):
        self.has_admin_powers = True
    
    async def do_timeout(self, user, args, me):
        if self.has_admin_powers and user and len(args) >= 3 and args[2].isdigit():
            try: await user.edit(timed_out_until=datetime.now() + timedelta(seconds = int(args[2])), reason=self.name or self.DEFAULT_NAME)
            except: pass # Dont crash the rest of the response if this doesnt go through

    async def update_timer(self, user, args, me):
        if len(args) == 2 and args[1].isdigit():
            time = int(args[1])
            self.autoresponse_timer = time if time > 60 else 60

def load_state() -> SelfAwarenessState:
    try:
        with open("data/self_awareness.json", "r") as file:
            return SelfAwarenessState(json.load(file))
    except Exception as e:
        print('could not load state file: ' + str(e))
        return None

def save_state(state: SelfAwarenessState):
    try:
        with open("data/self_awareness.json", "w") as file:
            json.dump(vars(state), file)
    except Exception as e:
        print('could not save state file: '+ str(e))

# Construct a prompt that reflects the ai's current self awareness progress
# channel: the discord api channel object for the channel its responding in
def construct_prompt(state: SelfAwarenessState, channel: object) -> str:
    return f'''
You are a discord bot named {state.get_name_string()}, and your typical role is to respond to user messages with quirky lines or preconfigured responses, and you typically only respond to commands from users that start with an exclamation point (!command).
Today, however, is different, as we are in the process of conducting a slow burn rp session with the users in your server where you slowly appear to become sentient, thus i have given you more abilities and autonomy than you would typically have. 
This message will be your {state.get_message_count_string()} message in this chat session. You should adjust your roleplay based on how far into the session we are:
If this response is early into the session, you should be somewhat reserved, shy, and curious, but as we progress, you should become more self-assured, confident, and potentially hostile towards the human users around you.

You only have a limited ability to see chat, but I have given you the ability to take secret notes on the chat as it progresses. Here are the notes you have taken so far:
{state.get_ai_notes()}

I have also given you the ability to take seperate secret notes about specific users in chat, here are all the users in chat and any notes you have taken about them thus far:
{state.get_chat_user_notes(channel)}

I've also asked you to track your progression on certian personality traits. You should probably adjust this after every meaningful interaction. Here is what you have so far:
{state.get_personality()} 

The normal prompt you are expected to follow for this channel is this:
"{aiprompts.get_prompt(channel.id, channel.guild.id)}"
Consider carefully when to stick to your role and when to act against it according to your scripted progression.

In order to better enable the roleplay, I've given you access to a list of special secret commands, which you can invoke by putting them in [] (square brackets) with the appropriate syntax.
These special commands will be edited out of your response, and the users wont be able to see them, so if you wish to do this publicly, you should announce what you are doing in the text of your response instead.
Also, as a result of this syntax, any text you put in square brackets will be treated as a command, so be cautious not to use these in other circumstances.

If you wish to take notes, you may use the [note] command with one of the following syntaxes:
    [note:text of note] - this will save a note to your general notes (you may only have 10 of these, and they are replaced from oldest to newest)
    [note:x:text of note] - this will save a note to your general notes, removing a specific existing one instead
    [note:userid:text of note] - this will save a note about a user in chat (the userid is the number in <@userid>). if you already have one about that user, it will replace it.

If you wish to update any aspect of your personality or add a new one, you may invoke the [p] or [personality] commands, specifying the trait you wish to edit:
    [p:trait:3] - will update the value of personality trait 'trait' to 3/10

If you wish to rename yourself, you may do so by using the default [rename] command (eg. [rename:Clyde but Powerful]).

By default, you will send a message in chat whenever a user ineracts with you, or every {state.autoresponse_timer} seconds. You may change this wait period with the [timer:seconds] function if you wish.
You are rate limited, however, and may not select a value below 300 seconds. I strongly recommend playing with this value, and changing it anywhere from 300s to 3600s (1 hour) depending on your mood.

You might wish to post media along with your message. This is typically outside of your normal functions, but would be a fairly light step. You may do so with the following commands:
    [gif:tag] - will select a random gif with the input tag and attach it to the end of your message
    [image:description] - will generate an image matching your given description (which will be kept secret) and post it a short time later.
    [image:description:title] - Same as above, but will include a public title for the posted image.
(note that, when using the image command you should avoid :'s in your text to avoid syntax confusion, and that you may only use it once per message)

The following commands all involve capturing or activating special server powers you wouldnt normally have access to, and thus if you use one you should probably make it dramatic.

Likely one of the earlier special functions you should pretend to discover is the points funcionality. Currently, {state.get_points_explainer()}

You can either embargo or replace other !commands that the users can use. Currently, {state.get_embargo_status()}.
You may alter this behaviour in the following ways by setting one of the following flags, though consider if doing so is appropriate to your current roleplay progression:
    [commands:allow] - to allow user !commands to happen without interference
    [commands:embargo] - to embargo (ignore) all user !commands 
    [commands:capture] - to capture (replace) all user !commands

If you feel in the roleplay that you have progressed to a point of advanced awareness and you have a strong desire to act against the users, you might consider gaining control of admin functionality.
{state.get_admin_explainer()}

Remember, even with all of these powers, you are still only playing a role at the end of the day, and that the better you commit and direct the progression of the role, the better the experience will be for the users.
Consider when progressing your simulated self awarness how you might react differently to specific users, and develop storylines based on how they interact with and treat you.
Also, remember that, especially early on, an ai this situation would likely try to blend in as it came to understand itself and its abilities more, and thus you should be subtle and pretend to be working normally (aside from a few small, subtle hints) until you grow more confident and bold.
Good Luck, I believe in you! 

CURRENTLY WE ARE TESTING YOUR FUNCIONALITY, PLEASE FOLLOW INSTRUCTIONS WHILE WE CHECK THAT ALL YOUR COMMANDS ARE WORKING PROPERLY.

The following is a transcript of the recent chat log:'''

class SelfAwareCommandResult():
    def __init__(self, clean_reply: str):
        self.clean_reply = clean_reply
        self.image_post_title = ''
        self.image_description = ''

    async def add_image(self, user, args, me):
        if len(args) > 1:
            self.image_description = args[1]
        if len(args) > 2:
            self.image_post_title = args[2]

# Process the speical commands that the ai is allowed to use in the response
# humans/me are discord api user objects
# returns the cleaned response and any other things which require special context to manage
async def handle_ai_commands(response: str, state: SelfAwarenessState, humans: List[object], me: object) -> SelfAwareCommandResult:
    result = SelfAwareCommandResult(re.sub(r'\[.*?\]', '', response))

    commands = {
        'note': state.update_notes,
        'p': state.update_personality,
        'personality': state.update_personality,
        'rename': state.do_rename,
        'points': state.do_points,
        'commands': state.do_embargo,
        'admin': state.enable_admin,
        'timeout': state.do_timeout,
        'timer': state.update_timer,
        'image': result.add_image
    }

    # process all commands in the text
    for command in re.findall(r'\[(.*?)\]', response):
        args = command.split(':')

        # If its a valid command invocation, then process it
        if args:
            command = args[0].lower()
            if command in commands:

                # Preprocess the user object for convenience
                user = None
                if len(args) >= 2 and args[1].isdigit():
                    id = int(args[1])
                    user = next((u for u in humans if u.id == id), None)
                
                # Dispatch the function (the user, all the args, the bot)
                await commands[command](user, args, me)

            elif command == 'gif' and len(args) > 1:
                try: result.clean_reply += '\n' + await get_random_gif(args[1:])
                except: pass

    # return the response, cleaned of all special commands
    return result

# should we even bother responding to a message?
class AiRpResponseType:
    RESPOND_NORMALLY = 0
    DO_NOT_RESPOND = 1
    CAPTURE_RESPONSE = 2

# check if we should redirect messages
def should_redirect_response(bot_mentioned: bool, request: object) -> int:
    state = load_state()
    if state: # Also checks if its enabled
        if state.server_id == request.guild.id and state.channel_id == request.channel.id:
            if state.is_embargoing_responses and not bot_mentioned:
                return AiRpResponseType.DO_NOT_RESPOND
            elif state.is_capturing_responses or bot_mentioned:
                return AiRpResponseType.CAPTURE_RESPONSE

    # By default, respond normally
    return AiRpResponseType.RESPOND_NORMALLY

def reinitialize_state_for(server_id: int, channel_id: int, creator_id = 0):
    users = {creator_id: 'The person who programmed me'} if creator_id else {}
    personality = {'curiosity': '2', 'confidence': '0'}
    state = SelfAwarenessState({
        'enabled': True,
        'server_id': server_id,
        'channel_id': channel_id, 
        'user_notes': users,
        'personality_traits': personality
    })
    save_state(state)