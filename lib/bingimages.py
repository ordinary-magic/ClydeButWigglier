# Code taken from a 3rd party library and then *heavily* modified to suit my purposes.
# https://github.com/acheong08/BingImageCreator

# OBSOLETED by openAI's DALLE integrations

import asyncio
import os
import random
import re
from io import BytesIO
from urllib.parse import quote

import aiohttp
from discord import File as dfile

BING_URL = os.getenv("BING_URL", "https://www.bing.com")

def get_headers():
    # Generate random IP between range 13.104.0.0/14
    forwarded_ip = (
        f"13.{random.randint(104, 107)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
    )
    return {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "max-age=0",
        "content-type": "application/x-www-form-urlencoded",
        "referrer": "https://www.bing.com/images/create/",
        "origin": "https://www.bing.com",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.63",
        "x-forwarded-for": forwarded_ip,
    }

# List of Bad (placeholder) images
bad_images = [
    "https://r.bing.com/rp/in-2zU3AJUdkgFe7ZKv19yPBHVs.png",
    "https://r.bing.com/rp/TX9QuO3WzcCJz1uaaSwQAz39Kb0.jpg",
]

class ImageGenAsync:
    """
    Image generation by Microsoft Bing
    Parameters:
        auth_cookie: str
    """

    def __init__(
        self,
        auth_cookie: str
    ) -> None:
        if auth_cookie is None:
            raise Exception("No auth cookie provided")
        self.session = aiohttp.ClientSession(
            headers=get_headers(),
            trust_env=True,
            cookies={"_U": auth_cookie}
        )
    async def __aenter__(self):
        return self

    async def __aexit__(self, *excinfo) -> None:
        await self.session.close()

    async def get_images(self, prompt: str) -> list:
        """
        Fetches image links from Bing
        Parameters:
            prompt: str
        """
        url_encoded_prompt = quote(prompt)
        # https://www.bing.com/images/create?q=<PROMPT>&rt=4&FORM=GENCRE
        url = f"{BING_URL}/images/create?q={url_encoded_prompt}&rt=4&FORM=GENCRE"
        payload = f"q={url_encoded_prompt}&qs=ds"
        async with self.session.post(url,allow_redirects=False,data=payload) as response:
            content = await response.text()
            if "this prompt has been blocked" in content.lower():
                raise Exception(
                    "Your prompt has been blocked by Bing. Try to change any bad words and try again.",
                )            
            if response.status != 302:
                # Fallback to rt3 if rt4 doesnt work
                url = f"{BING_URL}/images/create?q={url_encoded_prompt}&rt=3&FORM=GENCRE"
                async with self.session.post(url,allow_redirects=False,data=payload) as response2:
                    if response2.status != 302:
                        #print(f"ERROR: {await response2.text()}")
                        raise Exception("Redirect Failed")
                    else:
                        # Get redirect URL
                        redirect_url = response2.headers["Location"].replace("&nfy=1", "")
                        request_id = redirect_url.split("id=")[-1]
                    
            else:
                # Get redirect URL
                redirect_url = response.headers["Location"].replace("&nfy=1", "")
                request_id = redirect_url.split("id=")[-1]

        # Get the redirect
        (await self.session.get(f"{BING_URL}{redirect_url}")).close()
        
        # https://www.bing.com/images/create/async/results/{ID}?q={PROMPT}
        polling_url = f"{BING_URL}/images/create/async/results/{request_id}?q={url_encoded_prompt}"
        # Poll for results
        while True:
            # By default, timeout is 300s, change as needed
            async with self.session.get(polling_url) as response:
                if response.status != 200:
                    raise Exception("Could Not Get Results")
                content = await response.text()
                if content and content.find("errorMessage") == -1:
                    break

            await asyncio.sleep(1)
            continue

        # Use regex to search for src=""
        image_links = re.findall(r'src="([^"]+)"', content)
        # Remove size limit
        normal_image_links = [link.split("?w=")[0] for link in image_links]
        # Remove duplicates
        normal_image_links = list(set(normal_image_links))

        # Filter Out Placeholder Images
        image_links = [im for im in normal_image_links if im not in bad_images]
        if not image_links:
            raise Exception("No Images Generated")
        return image_links

    async def post_image(self, img_links, post_callback, prompt) -> None:
        """
        Posts Images to Discord
        Parameters:
            img_links: list[str]
            post_fun: the method to call to post the results
            prompt: str
        """
        try:
            images = []
            files = []
            for img_link in img_links:
                async with self.session.get(img_link) as response:
                    if response.status != 200:
                       raise Exception("Could not download image")

                    # Create file for image
                    image = BytesIO(await response.content.read())
                    images.append(image)
                    files.append(dfile(image, filename="image.jpg"))
            
            # Send the response
            await post_callback(content=f'"{prompt}"', files=files)

            # Close all the image objects
            map(BytesIO.close, images)

        except aiohttp.InvalidURL as url_exception:
            raise Exception(
                "Inappropriate contents found in the generated images. Please try again or try another prompt.",
            ) from url_exception

# User Cookie used to access the bing image generator api
ucookie = ''
def get_ucookie():
  global ucookie
  if ucookie == '':
    with open("keys/bing_ucookie.txt", "r") as token:
      ucookie = token.read()
  return ucookie

# Ask the Bing Image Generator to make an image for the prompt.
# prompt: the text to generate
# post_callback: the function to call when posting a response
async def get_rcb_image(prompt, post_callback):
    try: # Try to get and post the result
        async with ImageGenAsync(get_ucookie()) as image_generator:
            images = await image_generator.get_images(prompt)
            await image_generator.post_image(images, post_callback, prompt)
    except Exception as e:
        await post_callback(content=f'Bing API Error: {str(e)}')
