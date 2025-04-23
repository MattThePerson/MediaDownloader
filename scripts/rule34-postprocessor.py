import sys
import requests
from bs4 import BeautifulSoup as BS
from pathlib import Path
import os
import json
import shutil
import time

def main(path, post_id):

    # scrape metadata from post_id
    scraped_data = rule34_get_post_data(post_id)
    uploader = scraped_data.get('uploader')
    
    # read metadata file
    obj = Path(path)
    if obj.is_file():
        obj = obj.parent
    metadata_fp = os.path.join(str(obj), '.metadata', f'{post_id}.json')
    with open(metadata_fp, 'r') as f:
        metadata = json.load(f)
    
    # rename tag entry to 'tag_string'
    if 'tags' in metadata:
        # metadata['tags_string'] = metadata['tags']
        del metadata['tags']
    for k, v in scraped_data.items():
        metadata[k] = v
    
    # save data
    with open(metadata_fp, 'w') as f:
        json.dump(metadata, f, indent=4)
    
    # move files to uploader folder and delete old folder
    if uploader == None:
        raise Exception('ERROR: Uploader is None, cannot rename folder')
    
    oldparent = str(obj)
    newparent = os.path.join( obj.parent, uploader )
    print('Moving files from "{}" to "{}"'.format(obj.name, uploader))
    merge_folders(oldparent, newparent)
    

#### OTHER
def merge_folders(src_folder: str, dest_folder: str):
    src = Path(src_folder)
    dest = Path(dest_folder)
    
    for file in src.rglob('*'):
        if file.is_file():
            relative_path = file.relative_to(src)  # Get path relative to src_folder
            target_path = dest / relative_path  # Append relative path to dest_folder
            target_path.parent.mkdir(parents=True, exist_ok=True)  # Create subfolders if needed
            shutil.move(str(file), str(target_path))
    
    shutil.rmtree(src)


### SCRAPING ###

def parse_tag(el):
    classList = el.get('class').copy()
    classList.remove('tag')
    tagName = el.findAll('a')[-1].text
    return {'name': tagName, 'types': classList}

def get_tags(soup):
    tag_els = soup.findAll('li', {'class': 'tag'})
    tag_items = [ parse_tag(el) for el in tag_els ]
    tags = {}
    for tag in tag_items:
        tagType = tag['types'][0].split('-')[-1]
        arr = tags.get(tagType, [])
        arr.append(tag['name'])
        tags[tagType] = arr
    return tags

def get_uploader(soup):
    stats_el = soup.find('div', {'id': 'stats'})
    if stats_el == None:
        raise Exception('Couldnt find state_el (to find uploader name)')
    uploader = stats_el.findAll('li')[1].text.split('by')[1].strip()
    return uploader

def get_comments(soup):
    comment_list_el = soup.find('div', {'id': 'comment-list'})
    comment_els = comment_list_el.findAll('div', {'class': 'col2'})
    comments = [ el.text.strip() for el in comment_els ]
    return comments

def parse_data_from_soup(soup):
    data =  {
        'comments': get_comments(soup),
        'uploader': get_uploader(soup),
    }
    tags = get_tags(soup)
    for k, v in tags.items():
        newkey = 'tags_' + k
        data[newkey] = v
    return data

def rule34_get_post_data(post_id):
    url = 'https://rule34.xxx/index.php?page=post&s=view&id=' + post_id
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }
    res = None
    max_attempts = 5
    for att in range(max_attempts):
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            break
        else:
            print('[{}] Got status_code: {}, sleeping ...'.format(att+1, res.status_code))
            time.sleep(1)
    
    if res == None:
        raise Exception('Unable to scrape data from "{}" after {} attempts'.format(post_id, max_attempts))
    soup = BS(res.content, 'html.parser')
    data = parse_data_from_soup(soup)
    return data



if __name__ == '__main__':
    path = sys.argv[1]
    post_id = sys.argv[2]
    # print('Running rule34 postprocessor ...')
    main(path, post_id)