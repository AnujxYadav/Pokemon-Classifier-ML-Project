import asyncio
import os
import re
from string import Template
import bs4
import requests
import aiohttp

SCRAPE_URL = Template('https://replay.pokemonshowdown.com/search?user=&format=gen9ou&page=${page}&output=html')
BASE_URL = 'https://replay.pokemonshowdown.com'

async def download(log_url: str):
  id_ = re.search(r'(\d+)\.', log_url).groups()[0]
  if os.path.exists(f'datasets/logs/{id_}.log'):
    return
  
  async with aiohttp.ClientSession() as session:
    try:
      response = await session.get(log_url)
      text = await response.text()
      with open(f'datasets/logs/{id_}.log', 'w+', encoding='utf-8') as fl:
        fl.write(text)
    except aiohttp.client.ClientOSError:
      print(log_url)
    except aiohttp.client.ServerDisconnectedError:
      print('disconnected')
      return
    
async def main():
  async with asyncio.TaskGroup() as tg:
    for pnum in range(1, 25):
      page = requests.get(SCRAPE_URL.substitute(page=pnum))
      soup = bs4.BeautifulSoup(page.content, features='html.parser')
      ids = [x.get('href') for x in soup.find_all('a')]
      logs = [f'{BASE_URL}{id_}.log' for id_ in ids]
      for log in logs:
        tg.create_task(download(log))

if __name__ == '__main__':
  loop = asyncio.new_event_loop()
  asyncio.set_event_loop(loop)
  asyncio.run(main())
  