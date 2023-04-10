import argparse
import os
import subprocess
import re
import urllib.parse
import requests

import unearth

# 安装 unearth
# subprocess.run(['python3', '-m', 'pip', 'install', 'unearth'])

# 创建虚拟环境
# subprocess.run(['python3', '-m', 'venv', 'venv'])

parser = argparse.ArgumentParser()
parser.add_argument('--requirements', '-r', help='requirements file')
parser.add_argument('--pip', default='pip', help='pip path')
# todo: accept a python packages list

args = parser.parse_args()

# 解析requirements.txt
with open(args.requirements) as f:
    for line in f:
        # 获取包名
        line = line.strip()
        if not line:
            break
        if line.find('==') != -1:
            package_name, version = line.split('==')
        else:
            package_name, version = line, ''
        # 创建包名对应的文件夹
        os.makedirs(package_name, exist_ok=True)
        # 下载包
        if version:
            package_info = f'{package_name}=={version.strip()}'
        else:
            package_info = package_name
        subprocess.run([args.pip, 'download', package_info], cwd=package_name)

        # 解析架构包链接
        for filename in os.listdir(package_name):
            if re.match(rf'{package_name}-\d+\.\d+\.\d+.*\.(whl|tar\.gz)', filename):
                wheel_info = filename.split('-')
                wheel_arch = wheel_info[-2]
                if 'linux' in wheel_arch:
                    whl_file_path = os.path.join(package_name, filename)
                    whl_url = urllib.parse.urljoin('file:', urllib.request.pathname2url(os.path.abspath(whl_file_path)))
                    package_info = unearth.get_package_info(whl_url)
                    if package_info is not None:
                        # 下载不带架构的包
                        for download_info in package_info['downloads']:
                            if download_info['packagetype'] == 'sdist':
                                download_url = download_info['url']
                                r = requests.get(download_url, stream=True)
                                with open(os.path.join(package_name, download_url.split('/')[-1]), 'wb') as f:
                                    for chunk in r.iter_content(chunk_size=8192):
                                        if chunk:
                                            f.write(chunk)
                                break
