from typing import Any
import argparse # for typing
import sys
import subprocess
import shlex
from dataclasses import dataclass


@dataclass
class Global:
    last_login: str = ''


# Downloader
def gallerydl_downloader(args: argparse.Namespace, url: str, dest: str, settings: dict[str, Any]) -> int:
    command = get_gallerydl_command(url, dest, settings, redo_archived=args.redo_archived, skip_archived=args.skip_archived, extra_args=args.extra_args, presets=args.preset, config_file=args.gallerydl_config_file, playlist_range=args.limit_playlist)
    result = subprocess.run(shlex.split(command), stdout=sys.stdout, stderr=sys.stderr, cwd=args.scriptdir)
    return result.returncode


def get_gallerydl_command(url: str, dest: str, settings: dict[str, Any], skip_archived: bool=False, redo_archived: bool=False,
                            presets: str|None = None, config_file: str|None = None, playlist_range: str|None = None, extra_args: str|None = None, ):

    logins = settings.get('logins', {})

    options = [
        f'--destination "{dest}"',
        f'--cookies cookies/cookies.txt'
    ]
    if config_file:
        options.append(f'--config {config_file}')
        
    if redo_archived:
        options.append('-o skip=false') # redownload archived files
    
    if playlist_range:
        parts = playlist_range.split(':')
        if len(parts) == 1:
            start, end = 1, parts[0]
        else:
            start, end = parts[0], parts[1]
        end = int(end) + 1
        print('Limiting playlist range to:', playlist_range)
        options.append(f'--range {start}:{end}')
    
    if presets:
        preset_args = settings.get('presets', {}).get(presets)
        options.append(preset_args)
    
    site = get_url_site(url)
    if site:
        site_logins = logins.get(site)
        if site_logins:
            options.append( '--username ' + site_logins.get('username') )
            options.append( '--password ' + site_logins.get('password') )
            if site != Global.last_login:
                print(f"[COMMAND] Using logins for '{site}'")
                Global.last_login = site
    
    options_str = ' '.join(options)
    command = f'.venv/bin/gallery-dl {options_str} "{url}"'
    if extra_args:
        command += ' ' + ' '.join([ f'"{part}"' if ' ' in part else part for part in extra_args ])
    return command

def get_url_site(url):
    if 'x.com' in url:
        return 'twitter'
    if 'bsky.app' in url:
        return 'bluesky'
    # url = url.replace('https://', '')
    dot_parts = url.split('.')
    if len(dot_parts) < 2:
        return None
    return dot_parts[1]




