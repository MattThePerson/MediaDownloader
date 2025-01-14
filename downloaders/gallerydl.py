from typing import Any
import sys
import subprocess
import shlex
from dataclasses import dataclass


@dataclass
class Global:
    last_login: str = ''


# Downloader
def gallerydl_downloader(args, url, dest, logins):
    command = get_gallerydl_command(url, dest, logins, skip=args.skip, extra_args=args.extra_args)
    result = subprocess.run(shlex.split(command), stdout=sys.stdout, stderr=sys.stderr, cwd=args.scriptdir)
    return result.returncode


def get_gallerydl_command(url: str, dest: str, logins: dict[str, Any], skip: bool=False, extra_args: str|None = None):

    # dest = '/mnt/a/Whispera/gallery-dl'
    options = [
        '--config config/gallery-dl.conf',
        f'--destination "{dest}"',
    ]
    if not skip:
        options.append('-o skip=false') # redownload archived files
    
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
    command = f'venv/bin/gallery-dl {options_str} "{url}"'
    if extra_args:
        command += ' ' + ' '.join(extra_args)
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




