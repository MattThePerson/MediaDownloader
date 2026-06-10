from typing import List
import sys
import os
from pathlib import Path
import json
import subprocess
from pydantic import BaseModel, Field

class RedditComment(BaseModel):
    author: str
    body: str
    points: int
    replies: List["RedditComment"] = Field(default_factory=list)

class RedditPost(BaseModel):
    post_id: str
    subreddit: str = ""
    date_uploaded: str = ""
    title: str = ""
    post_body: str = ""
    author_username: str = ""
    comment_count: int = 0
    comments: List[RedditComment] = Field(default_factory=list)
    comments_html: str = ""

class Response(BaseModel):
    status_code: int
    message: str
    seconds_worked: float
    content: RedditPost | None = None

class Data(BaseModel):
    comments: List[RedditComment] = Field(default_factory=list)
    comments_html: str = ""


def _getRedditPost(post_id: str) -> RedditPost|None:
    cmd = [
        "/mnt/c/Users/stirl/.local/bin/reddit-post-scraper.exe",
        post_id,
        "--cookies-from-browser", "firefox",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)
    response = Response.model_validate(data)
    return response.content


def main(media_path, post_id):

    print('Getting reddit comments for: \'{}\' ... '.format(post_id), end='')

    # get post data
    post = _getRedditPost(post_id)
    if post is None:
        print("post object is None")
        sys.exit(1)
    print(f'found {post.comment_count} comments')

    data = Data(
        comments=post.comments,
        comments_html=post.comments_html,
    )

    # save coments
    metadata_fp = Path(media_path).parent / ".metadata" / f'{post_id}-comments.json'
    metadata_fp.parent.mkdir(exist_ok=True, parents=True)
    with open(str(metadata_fp), 'w') as f:
        f.write(data.model_dump_json(indent=4))

# start
if __name__ == '__main__':
    if len(sys.argv) > 3:
        if int(sys.argv[3]) > 1:
            exit(0)
    main(sys.argv[1], sys.argv[2])
