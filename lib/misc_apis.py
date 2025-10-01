from aiohttp import ClientSession
import json

async def get_random_wikipedia_article_name(amount:int = 1):
    url = f'https://en.wikipedia.org/w/api.php'
    params = {
        'action': 'query',
        'list': 'random',
        'format': 'json',
        'rnnamespace': 0,
        'rnlimit': amount
    }
    contents = json.loads(await get_url(url, params))
    return [x['title'] for x in contents['query']['random']]

async def get_url(url: str, params: dict) -> str:
    '''Get the full text contents of a given url'''
    headers = {
        'user-agent': 'ClydeButWigglier/1.0 (https://github.com/ordinary-magic/ClydeButWigglier)'
    }
    async with ClientSession() as session:
        async with session.get(url, params=params, headers=headers) as response:
            return await response.text()