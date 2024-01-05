# Giphy wrapper module
import json
import asyncio, aiohttp

# Get the secret giphy api key from a local file
apikey = ''
def get_giphy_apikey():
  global apikey
  if apikey == '':
    with open("keys/giphy_apikey.txt", "r") as token:
      apikey = token.read()
  return apikey

# Asynchronously get url of a random gif for the search keyword
async def get_random_gif(keyword):
  params = {'api_key': get_giphy_apikey(), 'tag': keyword}
  url = 'https://api.giphy.com/v1/gifs/random'
  async with aiohttp.ClientSession() as session:
    async with session.get(url, params=params) as response:
      gif = json.loads(await response.text())['data']
      return gif['url']
