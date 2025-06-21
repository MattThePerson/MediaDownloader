""" 
TODO:
- Make argument "-d ." for downloading in different directory work
"""
import re
import time
import subprocess
import shlex
# from pathlib import Path
import os
import argparse
from typing import Any
from datetime import datetime

from python.util import BookmarksGetter
from python.util import JsonHandler

from python.downloaders import gallerydl_downloader, _3dhentai_downloader


def tiktok_dl():
    print('doing NISH!')

Downloaders = {
    'gallery-dl': gallerydl_downloader,
    '3dhentai-dl': _3dhentai_downloader,
    'tiktok-dl': tiktok_dl,
}

__SCRIPTDIR__ = os.path.dirname(os.path.abspath(__file__))
__LOGFILE__ = os.path.join( __SCRIPTDIR__, 'data/activity.log' )


#region - MAIN ---------------------------------------------------------------------------------------------------------

def main(args: argparse.Namespace, settings: dict[str, Any]):
    
    # [STEP 0] HANDLE NON DOWNLOAD OPTIONS -------------------------------------

    continue_flag = True
    if args.gallery:
        subprocess.run(['gallery-dl', '-h'])
        
    elif args.settings:
        settings_fp = str(settings.get('settings_filepath'))
        if isinstance(args.settings, str):
            command = '{} "{}"'.format(args.settings, settings_fp)
            print(command)
            subprocess.run(shlex.split(command))
        else:
            print('Settings in "{}"\n'.format(settings_fp))
            with open(settings_fp, 'r') as f:
                for line in f:
                    if line.strip() != '':
                        print(line)
            print('\nTo edit settings pass program name (eg. -settings nano)')
        
    elif args.download_folder:
        df = settings.get('base-directory')
        if df:
            print('Opening download folder: "{}"\n'.format(df))
            open_in_explorer(df)
            # subprocess.run( [ 'explorer.exe', f'$(wslpath -w "{df}")' ] )
        else:
            print('Error: no base-directory')
    
    elif args.logs:
        print('\n #### DOWNLOAD LOG ####\n')
        for line in open(__LOGFILE__, 'r'):
            if line != '\n':
                print(line, end='')
        print()

    else:
        continue_flag = False # proceed to download
    if continue_flag:
        return
    
    
    # [STEP 1] GET URLS --------------------------------------------------------
    
    attempted_urls, _, failed_urls = get_download_log()
    
    urls_to_attempt: list[str] = []
    if args.url:
        urls_to_attempt.append(args.url)
    
    elif args.read_file: # -i, --input-file FILE       Download URLs found in FILE ('-' for stdin).
        print('[URLS] Feature not implemented')
        print(args.read_file)
        with open(args.read_file, 'r') as f:
            for line in f:
                urls_to_attempt.append(line.strip())
    
    elif args.bookmarks:
        print('[URLS] Retrieving urls from bookmarks ...')
        urls_to_attempt = get_urls_from_bookmarks(args, settings)
        
    elif args.from_logs:
        print('[URLS] Using attempted URLs ...')
        urls_to_attempt = attempted_urls
    
    else:
        print('Please give me urls, either through --bookmarks, --read-file or URL')
        return
    
    print('[URLS] Filtering {} urls ...'.format(len(urls_to_attempt)))
    if args.filters:
        filters = [ f.strip().lower() for f in args.filters.split(',') ]
        for filter_ in filters:
            urls_to_attempt = [ url for url in urls_to_attempt if filter_ in url.lower() ]
    
    if args.ignore_filters:
        ignore_filters = [ f.strip().lower() for f in args.ignore_filters.split(',') ]
        for filter_ in ignore_filters:
            urls_to_attempt = [ url for url in urls_to_attempt if filter_ not in url.lower() ]
    
    if args.redo_failed:
        urls_to_attempt = [ url for url in urls_to_attempt if url in failed_urls ]
    elif not args.redo:
        urls_to_attempt = [ url for url in urls_to_attempt if url not in attempted_urls ]
    
    if args.limit:      urls_to_attempt = urls_to_attempt[:args.limit]
    
    if urls_to_attempt == []:
        print('No urls got passed filtering')
        return


    # [STEP 2] DOWNLOAD --------------------------------------------------------
    
    dest = settings.get('base-directory', '')
    if args.destination:
        dest = args.destination
    print('Downloading media into: "{}"\n'.format(dest))
    
    succ: list[str] = []
    fail: list[str] = []
    times = []
    downloader_options: dict = settings.get('downloaders', {})
    for idx, url in enumerate(urls_to_attempt):
        
        downloader_func = None
        for exp, dl_name in downloader_options.items():
            if exp == '' or eval(exp):
                downloader_func = Downloaders.get(dl_name)
                break
        if downloader_func == None:
            print('ERROR: downloader_func is None')
            return
        if not (args.no_download and not args.down):
            print_url_download_info(idx, len(urls_to_attempt), url, len(succ), len(fail), times)
            start = time.time()
            returncode = downloader_func(args, url, dest, settings) # DOWNLOADER
            times.append(time.time() - start)
            print('Done. Took {:.1f}s. Returncode: {}'.format(times[-1], returncode))
            if returncode > 0:   fail.append(url)
            else:                succ.append(url)
            log_download(returncode, url, idx)
        else:
            print('({}/{}) "{}"'.format(idx+1, len(urls_to_attempt), url))
            if args.show_command:
                print("-command is DEPRECATED!!")
    
    return


#endregion

#region - HELPER FUNCS -------------------------------------------------------------------------------------------------

# get_urls_from_bookmarks
def get_urls_from_bookmarks(args: argparse.Namespace, settings: dict[str, Any]):
    
    bm_settings = settings.get('bookmarks')
    if bm_settings == None:
        print('[FAIL] No bookmarks settings in "settings.json"')
        exit(1)
    
    all_sites = [ site.lower() for site in bm_settings.keys() ]
    if args.bookmarks == True:
        sites = all_sites
    else:
        if args.bookmarks.lower() not in all_sites:
            print('[ERROR] No settings for site: "{}"'.format(args.bookmarks))
            exit(1)
        sites = [args.bookmarks]
    
    print('Getting bookmarks from following sites:', sites)
    bmGetter = BookmarksGetter()
    # urls: list[Any] = []
    bookmarks: list[dict[str, str]] = []
    for site in sites:
        site_settings = bm_settings.get(site)
        browser = bm_settings.get('browser', 'brave') # defaults to brave
        for folder in site_settings.get('folders', []):
            bookmarks.extend( bmGetter.get_bookmarks(browser, folder) )
    bookmarks.sort(key=lambda bm: bm['date_added'], reverse=(not args.reverse))
    urls = [ bm['url'] for bm in bookmarks ]
    return urls


## MISC HELPERS ##

def log_download(code, url, idx):
    global __LOGFILE__
    dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    folder = os.path.dirname(__LOGFILE__)
    if folder and not os.path.exists(folder):
        os.makedirs(folder)
    succ_str = 'CODE {:>2}{:<5}'.format(code, ' FAIL' if code > 0 else '')
    line_to_write = f'{dt} : {idx:<5} : {succ_str} : "{url}"'
    with open(__LOGFILE__, "a") as file:
        # if idx == 0:
        #     file.write('\n')
        file.write(line_to_write + "\n")

def get_download_log():
    all, only_succ, only_fail = [], [], []
    with open(__LOGFILE__, 'r') as f:
        for line in f:
            parts = [ p.strip() for p in line.replace('\n', '').split(' : ') ]
            url = parts[-1].replace('"', '')
            if url.startswith('https://'):
                failed = 'FAIL' in parts[-2]
                all.append(url)
                if not failed:
                    only_succ.append(url)
                else:
                    only_fail.append(url)
    return list(set(all)), list(set(only_succ)), list(set(only_fail))

def open_in_explorer(wsl_path):
    result = subprocess.run(["wslpath", "-w", wsl_path], capture_output=True, text=True)
    if result.returncode != 0:
        raise ValueError(f"Failed to convert path: {result.stderr.strip()}")
    windows_path = result.stdout.strip()
    subprocess.run(["explorer.exe", windows_path])

def print_url_download_info(idx, count, url, succN, failN, times):
    dt = datetime.now().strftime('%H:%M:%S')
    total_tt = format_time_difference(sum(times))
    average_tt = format_time_difference(sum(times) / len(times) if times != [] else 0)
    print(f'  [{dt}]  ({idx+1}/{count})  succ={succN}  fail={failN}  average_tt={average_tt}  total_tt={total_tt}')
    print(f'URL: "{url}"')

def format_time_difference(diff):
    h, rem = divmod(diff, 3600)
    m, s = divmod(rem, 60)
    ms = int((s % 1) * 1000)
    s = int(s)
    return f"{int(h):02}:" * (h > 0) + f"{int(m):02}:" + f"{s:02}.{ms:01}"


#endregion

#region - START --------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    print()
    parser = argparse.ArgumentParser("Wrapper utility for gallery-dl")
    
    parser.add_argument('-gallery', action='store_true', help='Show -h screen for gallery-dl')
    parser.add_argument('-settings', default=None, const=True, nargs="?", help='Print out settings (no args) or open in [nano, vim, code, ...]')
    parser.add_argument('--download-folder', '-df', action='store_true', help='Opens the download folder')
    parser.add_argument('-logs', action='store_true',help='Prints out logs')

    # [STEP 1] URL GETTINGS
    parser.add_argument('--url', '-u', help='[STEP 1] Pass url to download')
    parser.add_argument('--bookmarks', '-b', default=None, const=True, nargs="?", help='[STEP 1] Get urls from bookmarks')
    parser.add_argument('--read-file', '-r', help='[STEP 1] Pass file to read urls from')
    parser.add_argument('--from-logs', '-fl', action='store_true', help='[STEP 1] Retrievs list of urls from activity.log')
    
    # [STEP 2] URL FILTERING
    parser.add_argument('-limit', help='[STEP 2] Limit for how many urls to handle', type=int)
    parser.add_argument('-reverse', action='store_true', help='[STEP 2] Reverse order or urls') # NOTE: reverses in get bookmarks function
    parser.add_argument('-filters', help='[STEP 2] Filter URLs by strings (separate filters by comma ",")')
    parser.add_argument('--ignore-filters', help='[STEP 2] Filter URLs by strings to ignore')

    # [STEP 3] DOWNLOAD OPTIONS
    parser.add_argument('-preset', help='Use preset arguments for gallery-dl')
    parser.add_argument('--destination', '-d', help='Pass destination to download (default defined in settings.json)')
    parser.add_argument('-redo', action='store_true', help='[STEP 3] Retries urls even if previously attempted (according to activity.log)')
    parser.add_argument('-redo-failed', action='store_true', help='[STEP 3] Retries only urls found to have previously failed (according to activity.log)')
    parser.add_argument('-skip', action='store_true', help='[STEP 3] Skip links already downloaded or attempted (stored in archive.sqlite3)')

    parser.add_argument('--no-download', '-nd', action='store_true', help='Dont download, only list urls')
    parser.add_argument('-down', action='store_true', help='Counteracts --no-download')
    parser.add_argument('-show-command', action='store_true', help='Shows download command') # DEPRECATED !!
    
    parser.add_argument('-test', '--use-test-urls', action='store_true', help='Test downloading') # NOT IN USE
    parser.add_argument("extra_args", nargs=argparse.REMAINDER, help="Capture undefined arguments to pass to a shell script")
    
    # make args
    args = parser.parse_args()
    if args.extra_args:
        args.extra_args = args.extra_args[1:]
    args.scriptdir = __SCRIPTDIR__

    # process gallerydl config file (remove comments)
    gdl_config = 'config/gallery-dl.conf'
    gdl_config_comments = gdl_config + '.json'
    if os.path.exists(gdl_config_comments):
        with open(gdl_config_comments, 'r') as infile:
            content = infile.read()
            clean_content = re.sub(r'^\s*//.*', '', content, flags=re.M)
        with open(gdl_config, 'w') as outfile:
            outfile.write(clean_content)
    args.gallerydl_config_file = gdl_config
    
    # generate settings
    settingsHandler = JsonHandler('settings.json', readonly=True)
    settings = {}
    for k, v in settingsHandler.getItems():
        settings[k] = v
    loginHandler = JsonHandler('logins.json')
    settings['logins'] = loginHandler.jsonObject
    settings['settings_filepath'] = settingsHandler.filepath
    
    # handle download dir
    download_dir = settings.get('base-directory')
    if not download_dir:
        print('[SETTINGS] No base-directory defined in settings.json')
    elif not os.path.exists(download_dir):
        print('Download dir doesnt exist, making dirs:\n  "{}"'.format(download_dir))
        os.makedirs(download_dir, exist_ok=True)
    
    # gallery-dl presets
    if args.preset:
        preset_args = settings.get('presets', {}).get(args.preset)
        if preset_args == None:
            print('Preset called "{}" doesnt exist in settings.json'.format(args.preset))
            exit(1)
        else:
            print('Using gallery-dl presets: "{}"'.format(preset_args))
    
    # 
    if args.extra_args:
        print('Passing arguments to gallery-dl: "{}"'.format(args.extra_args))
    
    print()
    try:
        main(args, settings)
    except KeyboardInterrupt:
        print('\n\n[INTERRUPT] Script interrupted by user')
    print()

#endregion
