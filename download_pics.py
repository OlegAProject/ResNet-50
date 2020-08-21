import asyncio
import aiohttp
import os
import json
from json.decoder import JSONDecodeError
SEARCH_API_URL = "https://api.cognitive.microsoft.com/bing/v7.0/images/search"
SUBSCRIPTION_KEY = "f786a115361d4d3eb16d8d75f0998fe0"
SUBSCRIPTION_ENDPOINT = "https://api.cognitive.microsoft.com/bing/v7.0/search"
OFFSET = 100


class SashasApiException(Exception):
    pass


async def make_request(url, method, data, params=None, headers=None):
    async with aiohttp.ClientSession() as session:
        async with session.request(method=method, url=url, json=data, params=params, headers=headers) as resp:
            resp_data = await resp.text()
            try:
                resp_data = json.loads(resp_data)
            except JSONDecodeError:
                print('Invalid json data. Wrapping text.')
                resp_data = dict(text=resp_data)
            return resp.status, resp_data


async def download_content(url):
    async with aiohttp.ClientSession() as session:
        async with session.request(method="GET", url=url) as resp:
            return resp.status, await resp.content.read()


async def get(url, **kwargs):
    return await make_request(url, method='GET', data=None, **kwargs)


async def get_images_page(search_req: str, page_num: int = 0):
    status, data = await get(SEARCH_API_URL, params={"q": "apple fruit",
                                                     "count": 100,
                                                     "offset": OFFSET * page_num},
                             headers={"Ocp-Apim-Subscription-Key": SUBSCRIPTION_KEY})
    return status, data


async def images_generator(search_req, count):
    for page_num in range(0, int(count/OFFSET + 1)):
        status, data = await get_images_page(search_req, page_num)
        if status != 200:
            return
        for item in data['value']:
            thumbnail_url = item.get('thumbnailUrl')
            if thumbnail_url:
                status, data = await download_content(thumbnail_url)
                if status == 200:
                    yield data
                else:
                    print(f"Error reading image by url {thumbnail_url}")


async def save_images(search_req, count):
    im_counter = 0
    os.makedirs(f"images_{search_req}".replace(" ", "_"), exist_ok=True)
    async for image in images_generator(search_req, 100):
        path = f"images_{search_req}/{search_req}_{im_counter}.jpg".replace(" ", "_")
        with open(path, "w+b") as f:
            f.write(image)
        im_counter += 1


def save_images_sync(search_req, count):
    asyncio.get_event_loop().run_until_complete(save_images(search_req, count))

if __name__ == "__main__":
    save_images_sync("apple_fruit", 100)