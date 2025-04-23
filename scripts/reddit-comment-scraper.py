import sys


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
            if 'body' in item:
                comment_body = extract_text_from_markdown(item.get('body'))
                author = item.get('author')
                comments.append({'author': author, 'body': comment_body})
            for v in item.values():
                if isinstance(v, dict) or isinstance(v, list):
                    queue.append(v)
        elif isinstance(item, list):
            queue.extend(item)
    return comments

# 
def get_page_data(post_id, timeout=15, max_reps=3):
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
    if data == None:
        return None
    comment_objects = get_comments_from_data(data)
    ignore_users = ['AutoModerator']
    comments = [ obj['body'] for obj in comment_objects if obj['author'] not in ignore_users ]
    return comments

# 
def is_unwanted_comment(comment):
    if comment in ['[removed]', '[deleted]', 'Comment removed by moderator']:
        return True
    if "^^I'm ^^a ^^bot" in comment:
        return True
    return False


def main(media_path, post_id):
    print('Scraping reddit comments for: \'{}\' ... '.format(post_id), end='')
    metadata_dir = os.path.join( Path(media_path).parent, '.metadata')
    os.makedirs(metadata_dir, exist_ok=True)
    metadata_filepath = os.path.join( metadata_dir, f'{post_id}-comments.json'  )
    comments = get_comments_from_reddit_post(post_id)
    if comments == None:
        print("Getting comments didnt work! :'(")
        return
    comments = [ c for c in comments if not is_unwanted_comment(c) ]
    data = {'comments': comments}
    print('found {} comments'.format(len(comments)))
    with open(metadata_filepath, 'w') as f:
        json.dump(data, f, indent=4)


if __name__ == '__main__':
    
    if len(sys.argv) > 3:
        if int(sys.argv[3]) > 1:
            exit(0)
    
    import os
    from pathlib import Path
    import requests
    import time
    import markdown
    import json
    from bs4 import BeautifulSoup
    
    main(sys.argv[1], sys.argv[2])

