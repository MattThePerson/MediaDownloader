from typing import Any
import sys
import time
import requests
import os
import re
from pathlib import Path

from pornhub_api.api import PornhubApi

# given a phub viewkey and a directory, will save metadata about the phub video
# in the directory in a file called '{viewkey}.txt'
def main(viewkey, directory):
    print(f'Scraping PHub data for viewkey="{viewkey}" ... ', end='')
    try:
        data = fetch_video_data_phub(viewkey)
        metadata_filepath = os.path.join(directory, f'{viewkey}.txt')
        if data:
            data['upvotes'] = int(int(data['ratings']) * float(data['rating']))
            data['tags'] = [ t for t in data['tags'] if t.lower not in ['teen 18 1', '60fps 1'] ]
            with open(metadata_filepath, 'w') as f:
                for key in ["title", "uploader", "uploade_date", "views", "upvotes", "rating", "ratings", "tags", "categories", "pornstars"]:
                    f.write(f'{key}={str(data.get(key))}\n')
            print('Done.')
        else:
            print('FAILED')
    except:
        print('FAILED')


def fetch_video_data_phub(viewkey):
    if viewkey == None:
        print("    FAILED: ID is None:", viewkey)
        return None
    url = f'https://www.pornhub.com/view_video.php?viewkey={viewkey}'
    data = {'viewkey': viewkey}
    no_response = True
    response = None
    response = requests.get(url)
    for i in range(10):
        if response.status_code == 200:
            no_response = False
            uploader = extract_uploader_name_pornhub(response.content.decode())
            if uploader != None:
                data['uploader'] = uploader
                break
        time.sleep(0.4)
        response = requests.get(url)
    if 'uploader' not in data:
        if no_response:
            print("    FAILED: Response code not good:", response.status_code)
            return None
        else:
            print("    FAILED: No uploader found from response content")
            return None
    result: Any = None
    for i in range(10):
        try:
            result = PornhubApi().video.get_by_id(viewkey)
            break
        except ValueError as ve:
            time.sleep(0.4)
    if result == None:
        print("    VALUE_ERROR: Unable to get results from PornhubApi() for viewkey:", viewkey)
        return None
    data['title'] = result.title
    tags = [ t.tag_name for t in result.tags ]
    categories = [ " ".join(c.category.split("-")) for c in result.categories ]
    data['tags'] = tags
    data['categories'] = categories
    data['upload_date'] = str( result.publish_date )
    data['views'] = str( result.views )
    data['rating'] = str( result.rating )
    data['ratings'] = str( result.ratings )
    data['pornstars'] = [ ps.pornstar_name for ps in result.pornstars ]
    return data


def extract_uploader_name_pornhub(text):
    pattern = r"'video_uploader_name'\s*:\s*'([^']*)'"
    match = re.search(pattern, text)
    if match:
        uploader_name = match.group(1)
        return uploader_name
    else:
        return None



if __name__ == '__main__':
    
    directory = Path(sys.argv[1]).parent
    viewkey = sys.argv[2]
    main(viewkey, directory)