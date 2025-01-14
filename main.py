""" 
TODO:
- Make argument "-d ." for downloading in different directory work
"""
import time
import subprocess
from pathlib import Path
import os
import argparse
from typing import Any
from datetime import datetime
from util import BookmarksGetter
from util import JsonHandler

from downloaders import gallerydl_downloader, _3dhentai_downloader

Downloaders = {
    'gallery-dl': gallerydl_downloader,
    '3dhentai-dl': _3dhentai_downloader
}

__SCRIPTDIR__ = os.path.dirname(os.path.abspath(__file__))
__LOGFILE__ = os.path.join( __SCRIPTDIR__, 'data/activity.log' )


#### MAIN ####

def main(args: argparse.Namespace, settings: dict[str, Any]):
    
    # [STEP 0] HANDLE NON DOWNLOAD OPTIONS
    continue_flag = True
    if args.gallery:
        subprocess.run(['gallery-dl', '-h'])
        
    elif args.settings_path:
        print(settings['settings_filepath'])
        
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
    
    
    # [STEP 1] GET URLS
    
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
    if args.filter:
        urls_to_attempt = [ url for url in urls_to_attempt if args.filter.lower() in url.lower() ]
    
    if args.redo_failed:
        urls_to_attempt = [ url for url in urls_to_attempt if url in failed_urls ]
    elif not args.redo:
        urls_to_attempt = [ url for url in urls_to_attempt if url not in attempted_urls ]
    
    if args.limit:  urls_to_attempt = urls_to_attempt[:args.limit]
    
    if urls_to_attempt == []:
        print('No urls got passed filtering')
        return

    # [STEP 2] DOWNLOAD
    
    logins = settings.get('logins', {})
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
        else:
            if not (args.no_download and not args.down):
                print_url_download_info(idx, len(urls_to_attempt), url, len(succ), len(fail), times)
                start = time.time()
                returncode = downloader_func(args, url, dest, logins) # DOWNLOADER
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



# HELPER FUNCTIONS

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
    urls: list[Any] = []
    for site in sites:
        site_settings = bm_settings.get(site)
        browser = bm_settings.get('browser', 'brave') # defaults to brave
        for folder in site_settings.get('folders', []):
            bookmarks =  bmGetter.get_bookmarks(browser, folder)
            urls.extend([ bm['url'] for bm in bookmarks ])
    
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



# START
if __name__ == '__main__':
    parser = argparse.ArgumentParser("Wrapper utility for gallery-dl")
    
    parser.add_argument('-gallery', action='store_true', help='Show -h screen for gallery-dl')
    parser.add_argument('-settings_path', action='store_true', help='Print out settings')
    parser.add_argument('--download_folder', '-df', action='store_true', help='Opens the download folder')
    parser.add_argument('-logs', action='store_true',help='Prints out logs')

    parser.add_argument('--url', '-u', help='[STEP 1] Pass url to download')
    parser.add_argument('--bookmarks', '-b', default=None, const=True, nargs="?", help='[STEP 1] Get urls from bookmarks')
    parser.add_argument('--read_file', '-r', help='[STEP 1] Pass file to read urls from')
    parser.add_argument('--from_logs', '-fr', action='store_true', help='[STEP 1] Retrievs list of urls from activity.log')
    
    parser.add_argument('--destination', '-d', help='Pass destination to download (default defined in settings.json)')
    
    parser.add_argument('-limit', help='[STEP 2] Limit for how many urls to handle', type=int)
    parser.add_argument('-filter', help='[STEP 2] Filter URLs by string')
    # parser.add_argument('--site', help='Limit urls to site')

    parser.add_argument('-redo', action='store_true',help='[STEP 3] Retries urls even if previously attempted (according to activity.log)')
    parser.add_argument('-redo_failed', action='store_true',help='[STEP 3] Retries only urls found to have previously failed (according to activity.log)')
    # parser.add_argument('-noskip', action='store_true',help='[STEP 3] Dont skip links already downloaded or attempted (stored in archive.sqlite3)')
    parser.add_argument('-skip', action='store_true',help='[STEP 3] Skip links already downloaded or attempted (stored in archive.sqlite3)')

    parser.add_argument('--no_download', '-nd', action='store_true',help='Dont download, only list urls')
    parser.add_argument('-down',  action='store_true',help='Counteracts --only_list') # eh?
    parser.add_argument('-show_command', action='store_true',help='Shows download command')
    
    parser.add_argument('-test', '--use_test_urls', action='store_true', help='Test downloading')
    
    parser.add_argument("extra_args", nargs=argparse.REMAINDER, help="Capture undefined arguments to pass to a shell script")
    
    args = parser.parse_args()
    if args.extra_args:
        args.extra_args = args.extra_args[1:]
    
    args.scriptdir = __SCRIPTDIR__
    
    settingsHandler = JsonHandler('settings.json', readonly=True)
    
    download_dir = settingsHandler.getValue('base-directory')
    if not download_dir:
        print('[SETTINGS] No base-directory defined in settings.json')
    elif not os.path.exists(download_dir):
        print('Download dir doesnt exist, making dirs:\n  "{}"'.format(download_dir))
        os.makedirs(download_dir, exist_ok=True)
    
    settings = {}
    for k, v in settingsHandler.getItems():
        settings[k] = v
    
    loginHandler = JsonHandler('logins.json')
    settings['logins'] = loginHandler.jsonObject
    
    settings['settings_filepath'] = settingsHandler.filepath
    
    print()
    try:
        main(args, settings)
    except KeyboardInterrupt:
        print('\n\n[INTERRUPT] Script interrupted by user')
    print()
