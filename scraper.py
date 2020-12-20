import os, sys
import time

import requests
import json
import subprocess

from io import BytesIO
from bs4 import BeautifulSoup
from matplotlib import image as mpl_img
from PIL import Image

baseurl = 'https://www.ulta.com'

headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36'
}

# Product catalog (storage for all scraped data)
catalog = {}

# Links to each product page
product_links = []

# Swatch image directory
img_dir = 'img/ulta'

# First page
r = requests.get('https://www.ulta.com/nail-polish?N=278s', headers=headers)
soup = BeautifulSoup(r.content, 'lxml')

product_list = soup.find('ul', id='foo16').find_all('div', class_='productQvContainer')

for item in product_list:
    for link in item.find_all('a', class_='product', href=True):
        product_links.append(baseurl + link['href'])

# Second page
r = requests.get('https://www.ulta.com/nail-polish?N=278s&No=96&Nrpp=96', headers=headers)
soup = BeautifulSoup(r.content, 'lxml')

product_list = soup.find('ul', id='foo16').find_all('div', class_='productQvContainer')

for item in product_list:
    for link in item.find_all('a', class_='product', href=True):
        product_links.append(baseurl + link['href'].replace('https://www.ulta.com',''))

# Scrape data from each product
for i in range(len(product_links)):
        start_time = time.time()
        r = requests.get(product_links[i].strip(), headers=headers)
        soup = BeautifulSoup(r.content, 'lxml')

        # Check if product has shades
        img_div = soup.find_all('div', class_='ProductSwatches__Cell')
        if len(img_div) > 0:

            # Product name
            name = soup.find(
                    'div', class_='ProductMainSection__productName'
            ).find('span').text.strip()

            # Brand name
            brand = soup.find(
                    'p', class_='Text Text--body-1 Text--left Text--bold Text--small Text--$magenta-50').text.strip()

            # Product price
            price = soup.find('span', class_='Text Text--title-6 Text--left Text--bold Text--small Text--neutral-80').text.strip()
            
            # Add product info to catalog
            catalog[i] = {
                    'name': name,
                    'brand': brand,
                    'price': price[5:],
                    'url': product_links[i]
            }

            # Scrape RGB values of all shades
            catalog[i]['shades'] = {}
            for inner_div in img_div:
                img = inner_div.find('img')
                url = img['src'][:-7]
                img_content = requests.get(url, headers=headers)

                # Save swatch image
                with open("swatch.jpeg", "wb") as write_to:
                    write_to.write(img_content.content)

                # Clean shade name
                if img['alt'].endswith(' selected'):
                    shade_name = img['alt'][:-10]
                elif img['alt'].endswith('  '):
                    shade_name = img['alt'][:-2]
                else:
                    shade_name = img['alt']
                
                # Open image with pillow
                image = Image.open('swatch.jpeg')
                image.convert('RGB')

                # Crop image
                image = image.crop((170, 260, 330, 400))

                image_width, image_height = image.size

                r_total, g_total, b_total, count = 0, 0, 0, 0

                for x in range(0, image_width):
                    for y in range(0, image_height):
                        pixel_values = image.getpixel((x,y))
                        r = pixel_values[0]
                        g = pixel_values[1]
                        b = pixel_values[2]
                        r_total += r
                        g_total += g
                        b_total += b
                        count += 1

                r, g, b = round(r_total/count), round(g_total/count), round(b_total/count)
                catalog[i]['shades'][shade_name] = {}
                catalog[i]['shades'][shade_name]['colors'] = {'r': r, 'g': g, 'b': b}

                # Link to image of product in this shade
                shade_image_url = url[:-2]
                catalog[i]['shades'][shade_name]['image'] = shade_image_url

                # Delete swatch image
                os.remove('swatch.jpeg')
        else:
            print("Skipped!")

        print("Parsed link %s of %s (%s seconds)" % (i + 1, len(product_links), round(time.time() - start_time, 2)))

with open("ulta_catalog.json", "w") as outfile:
        json.dump(catalog, outfile)