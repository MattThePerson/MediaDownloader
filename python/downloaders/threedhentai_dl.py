from typing import Any
import argparse # for typing
import os
import urllib
import requests
from bs4 import BeautifulSoup as BS


def _3dhentai_downloader(args: argparse.Namespace, url: str, dest: str, settings: dict[str, Any]) -> int:
    """ Returns return code """
    data = get_info_3dhentai(url)
    if data:
        video_link = data.get('download_src')
        if not video_link:
            return 1
        dirname, filename = get_savepath_3dhentai(data)
        dirpath = os.path.join(*[dest, '3dHentai', dirname])
        savepath = os.path.join(dirpath, filename)
        metadata_filepath = os.path.join(dirpath, '{}.txt'.format(data.get('post_id')))
        print(f'Downloading from: "{video_link}"')
        print(savepath)
        os.makedirs(dirpath, exist_ok=True)
        save_metadata(metadata_filepath, data)
        ret = download_video(video_link, savepath)
        if ret:
            print('Success!')
            return 0
        else:
            print('DOWNLOAD FAILED')
            return 1
    return 1

def get_info_3dhentai(url):
    res = requests.get(url)
    if not (200 <= res.status_code and res.status_code < 300):
        print('ERROR: Unable to scrape info for url: "{}"'.format(url))
        return None
    soup = BS(res.content, 'html.parser')

    # get src
    data = {'url': url}
    try:
        video_link_end = str(soup).split('video=')[-1].split('"')[0]
        video_link = "https://3dhq1.org/video/3d/" + video_link_end
    except:
        print("ERROR: Unable to get src")
        return None
    data['download_src'] = video_link
    
    # post_id
    s1 = '<link href="'
    s2 = '" rel="shortlink"'
    SL = str(soup).split(s2)[0].split(s1)[-1]
    data['shortlink'] = SL
    data['post_id'] = SL.split('?p=')[-1]
    
    # get title
    title = soup.find('h1').get_text().strip()
    parts = title.split(' [')
    data['title'] = parts[0]
    if len(parts) > 1:
        data['title_artist'] = parts[1].split("]")[0].strip()
    
    # get artist
    try:
        artist = soup.find(id='video-cats').find('a').get_text()
    except:
        artist = data['title_artist']
        print("No artist on page, parsing from title:", artist)
    data['artist'] = artist

    # get characters
    characters_div = soup.find(id='video-actors')
    characters = []
    try:
        for atag in characters_div.find_all('a'):
            characters.append(atag.get_text())
    except:
        print("Unable to get characters")
    characters, ips = split_char_and_ip(characters)
    data['characters'] = characters
    data['sources'] = ips

    # date
    date_el = soup.find(id='video-date')
    date_str = date_el.get_text().replace('Added on:', '')
    date_fmt = format_date(date_str.strip(), delim='-')
    data['date_uploaded'] = date_fmt
    
    # tags
    tags_el = soup.find(id='video-tags')
    tags = []
    try:
        for atag in tags_el.find_all('a'):
            tags.append(atag.get_text())
    except:
        print("Unable to get tags")
    data['tags'] = tags
    
    # 
    if 'title_artist' in data:
        tags.append(data['title_artist'])
    
    return data


#### HELPERS ####

def download_video(video_link, savepath):
    urllib.request.urlretrieve(video_link, savepath)
    if not os.path.exists(savepath):
        return False
    return True

def get_savepath_3dhentai(data) -> tuple[str, str]:
    d = data.get('artist')
    fn = '[{}] {} [{}].mp4'.format( data.get('date_uploaded'), data.get('title'), data.get('post_id') )
    return d, fn

def format_date(date, delim='.'):
    pts = date.replace(',', '').split(" ")
    y = pts[-1]
    m = month_name_to_int(pts[0])
    if m < 10: m = f"0{m}"
    if len(pts) == 2:
        return "{}{}{}".format(y, delim, m)
    d = int(pts[-2])
    if d < 10: d = f"0{d}"
    return "{}{}{}{}{}".format(y, delim, m, delim, d)

def month_name_to_int(month):
    months = ['', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    month = month[:3].lower()
    return months.index(month)

def split_char_and_ip(characters):
    chars, ips = [], []
    for c in characters:
        splitter = ' ('
        parts = c.split(splitter)
        chars.append(parts[0])
        if len(parts) > 1:
            ips.append(parts[1].split(')')[0])
    return list(set(chars)), list(set(ips))

def save_metadata(fp, data):
    with open(fp, 'w') as f:
        for key in ["title", "url", "download_src", "artist", "characters", "sources", "tags"]:
            value = str(data.get(key))
            f.write(f'{key}={value}\n')
