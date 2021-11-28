import json
import os
import time

import requests
from bs4 import BeautifulSoup

LINKS_DUMPFILE = "data/links.json"

# Search and filter then paste url here:
SEARCH_LINK = "https://www.otomoto.pl/osobowe/seg-cabrio--seg-coupe/od-2013/"
HEADERS = {
    "headers": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:51.0) Gecko/20100101 Firefox/51.0"
}


def scrap_last_cars(search_link=SEARCH_LINK, headers=HEADERS):
    """Scrap first page of search.

    Args:
        search_link: Link to the search page. Defaults to SEARCH_LINK.
        headers: Headers for the requests. Defaults to HEADERS.

    Returns:
        dict: dictionary with scrapped data about the cars.
    """
    request = requests.get(search_link, headers=headers)
    soup = BeautifulSoup(request.content, "html.parser")
    items = soup.find_all("article", attrs={"class": "ds-ad-card-experimental"})

    links_dict = {}
    for item in items:
        time.sleep(0.01)
        item_dict = {}
        try:
            single_offer_link = item["data-href"]
            request = requests.get(single_offer_link, headers=headers)
            single_product_page = BeautifulSoup(request.content, "html.parser")

            item_dict["name"] = single_product_page.find(
                "span", attrs={"class": "offer-title"}
            ).text.strip()
            item_dict["img_link"] = single_product_page.find(
                "img", attrs={"class": "bigImage"}
            )["data-lazy"]

            price_str = single_product_page.find(
                "span", attrs={"class": "offer-price__number"}
            ).text.strip()
            price = price_str[:6].replace(" ", "")
            currency = price_str[-3:]
            item_dict["price"] = price + " " + currency

            main_params = single_product_page.find(
                "span", attrs={"class": "offer-main-params"}
            ).find_all("span")
            item_dict["year"] = main_params[0].text.strip()
            item_dict["km"] = main_params[1].text.strip()
            item_dict["body"] = main_params[3].text.strip()
            links_dict[single_offer_link] = item_dict
        except KeyError:
            pass

    return links_dict


def send_ad(context, chat_id, link, attributes):
    image_url = attributes["img_link"]
    name = attributes["name"]
    price = attributes["price"]
    year = attributes["year"]
    km = attributes["km"]
    body = attributes["body"]
    caption = f"{name}\n{price}; {year} rok; {km}; {body}; \n{link}"
    context.bot.send_photo(chat_id, image_url, caption=caption)


# 1, 2.
def prepare_dict(sync_previous=True):
    if sync_previous and os.path.isfile(LINKS_DUMPFILE):
        with open(LINKS_DUMPFILE, "r") as f:
            links_dict = json.load(f)
    else:
        links_dict = scrap_last_cars(SEARCH_LINK, HEADERS)
    return links_dict


# 3.
def send_new_ads(context, chat_id, links_dict):
    new_links_dict = scrap_last_cars(SEARCH_LINK, HEADERS)
    for link in new_links_dict:
        if link not in links_dict:
            send_ad(context, chat_id, link, new_links_dict[link])
            links_dict[link] = new_links_dict[link]
    return links_dict


# 4.
def dump_links(links_dict):
    json_object = json.dumps(links_dict, indent=4)
    with open(LINKS_DUMPFILE, "w") as f:
        f.write(json_object)
