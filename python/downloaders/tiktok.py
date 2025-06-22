from typing import Any
import argparse # for typing
import os
import subprocess
import json


def tiktok_downloader(args: argparse.Namespace, url: str, dest: str, settings: dict[str, Any]) -> int:
    """ Downloader for tiktok. Uses yt-dlp ... """

    # fetch metadata(s)
    metadata_cmd = [
        'yt-dlp',
        '--skip-download', '--print-json',
        # '--playlist-items', '1-4',
        url,
    ]
    if args.limit_playlist:
        parts = args.limit_playlist.split(':')
        if len(parts) == 1:
            start, end = 1, parts[0]
        else:
            start, end = parts[0], parts[1]
        print('Limiting playlist to:', args.limit_playlist)
        metadata_cmd.extend([
            '--playlist-items', f'{start}-{end}'
        ])
    
    print('fetching metadata ...')
    result = subprocess.run(
        metadata_cmd,
        capture_output=True,
        text=True,
    )
    metadatas = [ json.loads(line) for line in result.stdout.strip().splitlines() ]
    
    dirpath = dest + '/TikTok'
    
    for metadata in metadatas:

        # process metadata
        uploader = sanitize_filename(metadata['uploader'])
        title = sanitize_filename(metadata['title'])
        title_max_len = 120
        title = title if (len(title) <= title_max_len) else title[:title_max_len-3] + '...'
        upload_datetime = format_unix_time(metadata['epoch'])
        tiktok_id = metadata['id']

        bm = args.url_bookmark
        bookmark_tags = bm['location_relative'].split('/') if bm else []
        bookmark_tags = [ bm.replace(' ', '-') for bm in bookmark_tags ]
        tags_str = ' #' + ' #'.join(bookmark_tags) if bm else ''
        
        # download video using yt-dlp (also downloads metadata)
        command = [
            'yt-dlp',
            '--output', f'{dirpath}/{uploader}/[{upload_datetime}] {title} [%(id)s]{tags_str}.%(ext)s',
            metadata['webpage_url'],
        ]
        if not args.redo_archived:
            command.extend([
                '--download-archive', 'data/yt-dlp.archive'
            ])
        result = subprocess.run(command)
        if result.returncode != 0:
            return result.returncode
        
        # save metadata
        metadata_dirpath = f'{dirpath}/{uploader}/.metadata'
        os.makedirs(metadata_dirpath, exist_ok=True)
        metadata_file = f'{metadata_dirpath}/{tiktok_id}.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=4)
        
        # scrape a few comments
        ...
    # return 0



    return 0


def format_unix_time(epoch, fmt="%Y-%m-%d %H꞉%M꞉%S"):
    from datetime import datetime
    return datetime.fromtimestamp(epoch).strftime(fmt)

def sanitize_filename(name):
    replacements = {
        '/': '⧸',
        '\\': '⧹',
        '?': '？',
        '%': '％',
        '*': '∗',
        ':': '꞉',
        '|': '∣',
        '"': '＂',
        '<': '＜',
        '>': '＞',
    }
    return ''.join(str(replacements.get(c, c)) for c in name)
