import argparse
import io
import os
import re
import uuid

import requests
from PIL import Image


# This function downloads an image from a given URL and saves it to a local directory
# It takes a URL as input
# It returns the path to the downloaded image file

def download_img(url):
    # Send a GET request to the URL and store the response
    response = requests.get(url)
    # Print the response status code for debugging purposes
    print(response)
    # Determine the file extension of the image from the URL
    file_ext = os.path.splitext(url)[-1]
    # If the file extension cannot be determined from the URL, open the image using PIL and get the format
    if not file_ext:
        img = Image.open(io.BytesIO(response.content))
        file_ext = '.' + img.format.lower()
    # Generate a unique name for the image file using UUID
    img_name = str(uuid.uuid4()) + file_ext
    # Create a directory to store the images if it doesn't exist
    img_dir = 'images'
    os.makedirs(img_dir, exist_ok=True)
    # Create the full path to the image file
    img_path = os.path.join(img_dir, img_name)
    # Write the image content to the file
    with open(img_path, 'wb') as f:
        f.write(response.content)
    # Return the path to the downloaded image file
    return img_path

def replace_img(markdown_path):
    # read the content of the markdown file
    with open(markdown_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # find all image urls in the markdown file
    pattern = r'!\[.*?\]\((.*?)\)'
    for url in re.findall(pattern, content):
        # download the image if it's from a url and replace the url with the path to the downloaded image
        if url.startswith('http'):
            img_path = download_img(url)
            content = content.replace(url, img_path)
    # write the modified content back to the markdown file
    with open(markdown_path, 'w', encoding='utf-8') as f:
        f.write(content)


if __name__ == '__main__':
    # use argparse to add an argument to accept a markdown file as input
    parser = argparse.ArgumentParser()
    parser.add_argument('--markdown_file', '-f', help='path to the markdown file')
    args = parser.parse_args()

    # replace all image urls in the markdown file with the path to the downloaded image
    replace_img(args.markdown_file)
