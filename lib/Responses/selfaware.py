import asyncio
from .response import ResponseInterface
from lib import selfawareness, aiapi
from lib.discord_helpers import get_history, package_discord_images

class ThreadSafeLock:
    def __init__(self):
        self._lock = None

    def __call__(self):
        if self._lock is None: # If i multithread this ever, i need to use a differnt lock.
            self._lock = asyncio.Lock()
        return self._lock

# Initialize once (e.g., in bot setup)
self_aware_single_state_lock = ThreadSafeLock()

class SelfAwareResponse(ResponseInterface):
	callsign = '_selfaware'

	# Generate a chat completion reply to the existing chat log
	async def respond_to_message(self, text, request):
		request.content = text
		messages = [request] + await get_history(request.channel, limit=10, before=request)
		messages.reverse()
		
		return await self.get_common_response(messages, request.channel)
		
	# The autofire resposne entry point
	async def autofire_response(self, channel):
		messages = await get_history(channel, limit=10)
		messages.reverse()
		return await self.get_common_response(messages, channel)
		
	# Common response handling method
	async def get_common_response(self, messages, channel):
		all_users = channel.members
		humans = [user for user in all_users if (not user.bot)]
		me = next(user for user in all_users if self.is_me(user))
		async with self_aware_single_state_lock():
			state = selfawareness.load_state()
			prompt = selfawareness.construct_prompt(state, channel)
			response = await aiapi.respond_to_messages_with_customized_prompt(messages, prompt, self.is_me)
			self.log(response) # Log the unedited version of the response, before the special commands are removed
			response = await selfawareness.handle_ai_commands(response, state, humans, me)
			self.run_in_background(self.check_for_additional_posts(response, channel))
			self.inactivity_autofire = state.autoresponse_timer
			selfawareness.save_state(state)
			return response.clean_reply
		
	# check for and perform any additional posts required
	async def check_for_additional_posts(self, response: selfawareness.SelfAwareCommandResult, channel):
		# Check for images
		if response.image_description:
			image, err = await aiapi.get_image_generation(response.image_description)
			if image:
				images = package_discord_images([image])
				if response.image_post_title: # Titles are optional
					await channel.send(content=response.image_post_title, files=images)
				else:
					await channel.send(files=images)
			else:
				await channel.send(content=err)