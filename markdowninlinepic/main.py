import argparse
import io
import os
import re
import hashlib

import requests
from PIL import Image


# This function downloads an image from a given URL and saves it to a local directory
# It takes a URL as input
# It returns the path to the downloaded image file
def download_img(url, directory = None, host = None):
    # Edit the URL
    if host:
        pattern = r"(localhost|127\.0\.0\.1)(?::[0-9]+)?"
        if re.search(pattern,url):
            url = re.sub(pattern, host, url)
    # Send a GET request to the URL and store the response
    response = requests.get(url)
    # Print the response status code for debugging purposes
    print(response)
    # Claculate the MD5 hash of the image file
    md5_hash = hashlib.md5(response.content)
    md5_digest = md5_hash.hexdigest()
    # Determine the file extension of the image from the URL
    file_ext = os.path.splitext(url)[-1]

    # If the file extension cannot be determined from the URL, open the image using PIL and get the format
    if not file_ext:
        img = Image.open(io.BytesIO(response.content))
        file_ext = '.' + img.format.lower()

    # Generate a unique name for the image file using UUID
    img_name = md5_digest + file_ext

    # Create a directory to store the images if it doesn't exist
    if directory:
        img_dir = os.path.join(directory,'images')
    else:
        img_dir = 'images'
    os.makedirs(img_dir, exist_ok=True)

    # Create the full path to the image file
    img_path = os.path.join(img_dir, img_name)

    # Write the image content to the file
    with open(img_path, 'wb') as f:
        f.write(response.content)
    img_path = os.path.join("images", img_name)
    # Return the path to the downloaded image file
    return img_path


# This function replaces image URLs in a markdown file with the path to the downloaded image
# It takes a markdown file path as input
def replace_img(markdown_path, host=None):
    # read the content of the markdown file
    with open(markdown_path, 'r', encoding='utf-8') as f:
        content = f.read()
    directory,_ = os.path.split(markdown_path)
    # find all image urls in the markdown file
    pattern = r'!\[.*?\]\((.*?)\)'
    for url in re.findall(pattern, content):
        # download the image if it's from a url and replace the url with the path to the downloaded image
        if url.startswith('http'):
            img_path = download_img(url, directory = directory, host = host)
            content = content.replace(url, img_path)

    # write the modified content back to the markdown file
    with open(markdown_path, 'w', encoding='utf-8') as f:
        f.write(content)


if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--markdown_file', '-f', nargs="+", help='path to the markdown files')
    parser.add_argument('--markdown_folder', '-d', nargs="+", help='folder to the markdown files')
    parser.add_argument('--host', help = 'specify the host')
    file_list = []
    args = parser.parse_args()
    host = args.host
    for file in args.markdown_file:
        file_list.append(file)
    for folder in args.markdown_folder:
        for root, dirs, files in os.walk(folder):
            for f in files:
                if f.endswith('.md'):
                    mdfile_path = os.path.relpath(os.path.join(root, f), os.getcwd())
                    file_list.append(mdfile_path)
    # Replace image URLs in each markdown file
    for each in file_list:
        replace_img(each, host=host)
