import asyncio
from datetime import datetime, timedelta
from typing import Tuple

class ResponseInterface:
	callsign = '' # The flag to register this response for

	blurb = '' # help text blurb to describe the response
	
	# Delegate method used to run a call asynchronously in in a new thread and get a result
	run_thread = None # async def run_thread(func, *args) -> result
	
	# Delegate method used to run an awaitable in the background without waiting for it
	run_in_background = None # self.run_in_background(some_awaitable_task())

	# Delegate method used to determine if a user is the bot
	is_me = None # def is_me(id) -> boolean

	# Reference to the discord post method
	post = None
	
	# Data required by rate limiting of the responses
	cooldown = timedelta(-20) # Default Cooldown is negative in case of race conditions
	last_use = datetime.min # Last use of the response
	manual_timer = False # If True, responses will handle their own timers (check is skipped)

	# Autofire controls (allows responses to trigger themselves after a number of seconds of inactivity)
	inactivity_autofire = 0 # if this is < 30 autofires will not happen
	last_message_at = None
	autofiring = False
	
	# Logging controls (if true, will log every response in logs/response.txt)
	log_response = False
	
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
	async def respond_with_context(self, text: str, request: object, channel: object) -> Tuple[str, object]:
		return await self.respond_to_message(text, request), request

	# Entry point into the class. Will check the cooldown first, then call the response chain
	# Will Return (Message Text, Optional Message to Reply To, Extra kwargs for post command)
	async def get_response(self, text, request, channel):
		if self.manual_timer or self.check_cooldown_timer():
			response = await self.respond_with_context(text, request, channel)
			if self.log_response:
				self.log(response[0])
			self.last_message_at = datetime.now()
			return response
		else:
			return ['!{} is on cooldown ({}s left)'.format(
				self.callsign, self.get_cooldown_time()), request]
	
	# Autofire response will provide the channel which we are responding to and nothing else
	# Should return a string containing the response.
	async def autofire_response(self, channel: object) -> str:
		return ''
	
	# Peroform the autofire delay loop
	# Currently only posts in one channel but that works for now
	async def perform_autofire(self, channel: object):
		while self.inactivity_autofire > 30:
			self.autofiring = True
			wait_period = self.last_message_at + timedelta(seconds = self.inactivity_autofire) - datetime.now()
			if wait_period > timedelta(): # > 0, basically
				await asyncio.sleep(wait_period.total_seconds() + 1)
			else:
				text = await self.autofire_response(channel)
				if text:
					await self.post(text, channel, {}, is_reply=False)
				self.last_message_at = datetime.now()
		self.autofiring = False

	# Check if the cooldown timer has elapsed, updating it on success
	def check_cooldown_timer(self):
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
	
	# Logging function, can either be enabled automatically or invoked manually
	def log(self, text: str):
		with open(f"logs/{self.callsign}.log", "a") as logfile:
			logfile.write(datetime.now().strftime("%y/%m/%d %H:%M:%S.%f") + ":\n")
			logfile.write(text + "\n")