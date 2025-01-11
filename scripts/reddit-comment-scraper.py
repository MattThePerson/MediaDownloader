import sys
import os
from pathlib import Path
import requests
import time
import markdown
from bs4 import BeautifulSoup

# 
def extract_text_from_markdown(markdown_text):
    html = markdown.markdown(markdown_text)
    soup = BeautifulSoup(html, 'html.parser')
    return soup.get_text()

# 
def get_comments_from_data(data):
    comments = []
    queue = data.copy()
    while queue != []:
        item = queue.pop(0)
        if isinstance(item, dict):
            for k, v in item.items():
                if k == 'body':
                    comments.append(extract_text_from_markdown(v))
                else:
                    queue.append(v)
        elif isinstance(item, list):
            queue.extend(item)
    return comments

# 
def get_page_data(post_id, timeout=5, max_reps=3):
    if max_reps == 0:
        return None
    page_url = f"https://www.reddit.com/comments/{post_id}.json"
    res = requests.get(page_url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    })
    if res.status_code == 429:
        print(f'[REDDIT COMMENT SCRAPER] Status code 429 (Too Many Requests). Sleeping for {timeout} sec ...')
        time.sleep(timeout)
        return get_page_data(post_id, timeout=timeout, max_reps=max_reps-1)
    elif res.status_code == 404:
        print('[REDDIT COMMENT SCRAPER] Error 404')
        return None
    return res.json()

# 
def get_comments_from_reddit_post(post_id):
    data = get_page_data(post_id)
    comments = get_comments_from_data(data)
    return comments


def main(media_path, post_id):
    print('[REDDIT COMMENT SCRAPER] Scraping reddit comments for post: \'{}\' ... '.format(post_id), end='')
    metadata_filepath = os.path.join( Path(media_path).parent, f'{post_id}.txt' )
    comments = get_comments_from_reddit_post(post_id)
    if comments == None:
        print('THAT DIDNT WORK')
    else:
        print('found {} comments'.format(len(comments)))
        with open(metadata_filepath, 'a') as f:
            for comment in comments:
                if comment not in ['[removed]', '[deleted]', 'Comment removed by moderator'] and "^^I'm ^^a ^^bot." not in comment:
                    comment = comment.replace('\n', '')
                    f.write(f'comment="{comment}"\n')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

