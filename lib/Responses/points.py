from .response import ResponseInterface
from lib.serverdata import ServerDatabase
from lib.discord_helpers import get_username_from_id
from datetime import datetime, timedelta

POINT_APPOINTEE = 'point_appointee'
DEPUTY_POINT_APOINTEE = 'deputy'

class Points(ResponseInterface):
    callsign = 'points'
    blurb = 'award and track points given to users'
    deputy_timeout = datetime.min

    async def respond_to_message(self, text, request):
        #Determine which mode to use, and send it to the appropriate function

        # !points
        if len(text.strip()) == 0:
            return self.ranking(request.channel)

        # Try to parse the formatted commmand
        parts = text.strip().split(' ', 1)
        command = parts[0].lower()
        serverid = request.guild.id

        # All other commands require authorization
        if not self.is_appointed(request.author.id, serverid, command == 'add'):
            return "Sorry, you don't have clearance for that. :spy:"

        # Reset the points
        if 'reset' == command:
            self.reset(serverid)
            return f"Everyone's hard-earned {self.name(serverid)} have been reset! :disguised_face:"

        # Get a List of Targets
        targets = [x.id for x in request.mentions]

        # Check if we have enough parts for other stuff
        if len(parts) < 2 or len(targets) == 0:
            return "Woah friendo, seems like you typoed something. Check \"!help points\" and try again. :sweat:"

        # Appoint someone
        if 'appoint' == command:
            if request.author.id == targets[0]:
                return "You can't Point-Appoint yourself! Thats Illegal!"
            return self.point_appoint(serverid, targets[0], parts[1].split(' <@')[0])
            
        # check for bad commands before we assume a number    
        if parts[0] != 'add' and parts[0] != 'deputize':
            return "Woah friendo, seems like you typoed something. Check \"!help points\" and try again. :pensive:"

        # Parse Number Options
        try: amount = float(parts[1].split(' ')[0])
        except ValueError: return f"Sorry, but \"{parts[1].split(' ')[0]}\" isnt a valid floating point number. :nerd:"

        # Add Points (respond via emoji, not text)
        if 'add' == command:
            self.add_points(request.guild.id, targets, amount)
            await request.add_reaction("✅")
            return None

        # Deputize Someone
        if 'deputize' == command:
            if request.author.id == targets[0]:
                return "You can't nominate yourself Point-Appointee and Deputy Point-Appointee! Thats Illegal!"
            return self.deputize(serverid, targets[0], amount)
            
        return "Woah pal, seems like you typoed something. Check \"!help points\" and try again. :pensive:"

    # Increase (or decrease) the point totals of the specified users
    def add_points(self, serverid, targets, amount):
        with ServerDatabase(serverid) as db:
            for id in targets:
                db.add_to_value(id, 'points', amount)

    # Deputize a user to authorize them to add points
    def deputize(self, serverid, target, amount):
        self.deputy_timeout = datetime.now() + timedelta(minutes=amount)
        with ServerDatabase(serverid) as db:
            old_dep = db.get_special_user(DEPUTY_POINT_APOINTEE, 'point_role')
            db.set_value(old_dep, 'point_role', '')
            db.set_value(target, 'point_role', DEPUTY_POINT_APOINTEE)
        return f"<@{target}> has been appointed loyal Deputy-Point-Apointee of {self.name(serverid)}! (for the next {amount} minutes anyway) :cowboy:"

    # Check if a user is authorized for a command
    def is_appointed(self, userid, serverid, deputy=False):
        with ServerDatabase(serverid) as db:
            point_appointee = db.get_special_user(POINT_APPOINTEE, 'point_role')
        return point_appointee is None or userid == point_appointee or \
            (deputy and self.is_deputized(userid, serverid))

    # Check if a user is currently deputized
    def is_deputized(self, userid, serverid):
        with ServerDatabase(serverid) as db:
            return datetime.now() < self.deputy_timeout and \
                userid == db.get_special_user(DEPUTY_POINT_APOINTEE, 'point_role')

    # Retrieve the current name for of the point system
    def name(self, serverid):
        with ServerDatabase(serverid) as db:
            return db.get_value(0, 'point_name', 'static_vars') or "points"
    
    # Name someone as the new Point-Appointee in the server's database
    def point_appoint(self, serverid, target, name):
        with ServerDatabase(serverid) as db:
            db.initialize_column('point_role', '') # wipe old appointee and deupty
            db.set_value(target, 'point_role', POINT_APPOINTEE)
            db.set_value(0, 'point_name', name, 'static_vars')
        
        self.deputy_timeout = datetime.now()
        return f":tada: Let it be known that from this day forth, <@{target}> shall be ruler and Chief Point-Apointee of \"{name}\"! :tada:"
    
    # Retrieve the user's point totals in ranked order
    def ranking(self, channel):
        with ServerDatabase(channel.guild.id) as db:
            scores = sorted(db.get_points(), key=lambda x: x[1], reverse=True)
        name = self.name(channel.guild.id)

        result = 'The Current Scores Are:'
        for count, (id, score) in enumerate(scores):
            result += f'\n{count+1}. {round(score, 3)} {name} - {get_username_from_id(id, channel)}'
        
        if not '\n' in result:
            return "Nobody has any points yet :("
        return result
    
    # Reset the server's scores
    def reset(self, serverid):
        with ServerDatabase(serverid) as db:
            db.initialize_column('points', 0.0)
 
    # Get the help text for the module
    def get_help(self):
        return f'General !{self.callsign} Commands:\n' +\
               f'> "!{self.callsign}" will display the current point rankings.\n' + \
               f'\n' + \
               f'Point-Appointee and Deputy Commands\n' + \
               f'> "!{self.callsign} add ## @user [@user2...]" will add (or subtract) points from specified user(s).\n' + \
               f'\n' + \
               f'Point-Appointee Only Commands:\n' + \
               f'> "!{self.callsign} reset" will reset the point total.\n' + \
               f'> "!{self.callsign} appoint <name> @User" will make someone the new Point-Appointee and change the name to <name>.\n' + \
               f'> "!{self.callsign} deputize <minutes> @User" will appoint someone as the Deputy-Point-Appointee for <number> minutes.\n' + \
               f'\n' + \
               f'Note: @user can be omitted if you are replying to a message.'
               