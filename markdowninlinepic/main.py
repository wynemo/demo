import argparse
import os
import re
import uuid

import requests

def download_img(url):
    # generate a unique name for the image file
    img_name = str(uuid.uuid4()) + os.path.splitext(url)[-1]
    # create a directory to store the images if it doesn't exist
    img_dir = 'images'
    os.makedirs(img_dir, exist_ok=True)
    # create the full path to the image file
    img_path = os.path.join(img_dir, img_name)
    
    # download the image from the url and save it to the image file
    with open(img_path, 'wb') as f:
        r = requests.get(url)
        print(r)
        f.write(r.content)
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
