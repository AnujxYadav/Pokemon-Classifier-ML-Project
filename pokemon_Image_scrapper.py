import requests
from bs4 import BeautifulSoup
import os

url = "https://play.pokemonshowdown.com/sprites/dex/"

resp = requests.get(url)
images = resp.content

soup = BeautifulSoup(images, "html.parser")
image_url = []
for link in soup.find_all("a"):
    href = link.get("href")
    if href.endswith(".png"):
        image_url.append(url + href)

if not os.path.exists("pokemon_images"):
    os.makedirs("pokemon_images")

for image_url in image_url:
    resp = requests.get(image_url)
    image_name = image_url.split("/")[-1]
    with open("pokemon_images/" + image_name, "wb") as f:
        f.write(resp.content)









        