'''Useful Functions common across test classes'''
import discord, asyncio
from unittest.mock import Mock
  
# Construct a bare mockery of a discord message with the requested fields
def get_mock_discord_message(author_id=0, mentions=[]):
  # Mock the message and add required fields
  mock_request = Mock(spec=discord.Message)
  mock_request.mentions = [get_mock_user(x) for x in mentions]
  mock_request.author = get_mock_user(author_id)
  
  # Return the mockery
  return mock_request
  
# Construct a bare mockery of a discord user
def get_mock_user(id):
  user = Mock(spec=discord.User)
  user.id = id
  return user
  
# Call a response object's get_response method synchronously
def get_response(test_object, text, context):
  return asyncio.run(test_object.get_response(text, context, None))