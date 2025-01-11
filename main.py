import time
import subprocess
import shlex
import sys
import os
import argparse
from typing import Any
from datetime import datetime
from util import BookmarksGetter
from util import JsonHandler

__SCRIPTDIR__ = os.path.dirname(os.path.abspath(__file__))
__LOGFILE__ = os.path.join( __SCRIPTDIR__, 'data/activity.log' )

""" 
TODO:
- Make argument "-d ." for downloading in different directory work
"""



""" TESTS """
def get_test_urls():
    TEST_URLS = [
        # TWITTER 0-5
        'https://x.com/EroticNansensu/status/1876358077525770543',
        'https://x.com/cyanafterhours/status/1873931176731451493/', # two images, quote tweet
        'https://x.com/SenseiAnother/status/1876256590954950696', # video
        'https://x.com/die_scope/status/1876347523205628156', # HashTags

        'https://x.com/emiillb/status/187636099975186', # Doesnt exits
        'https://x.com/AfterDarkWasa/status/1876469006116487184', # NO MEDIA, JUST TWEET

        # REDDIT 6-13
        'https://www.reddit.com/r/LenaPaul/comments/1hv9c96/lena_riding/', # gif
        'https://www.reddit.com/r/LenaPaul/comments/1hvm8b7/fucking_lena_nonstop/', # gif
        'https://www.reddit.com/r/InvaderVie/comments/1hvmujx/hotter_than_ever/', # multiple images
        'https://www.reddit.com/r/GOONED/comments/1hve0ld/2025_year_of_the_gooners_tell_me_your_favorite_3/', # multiple gifs
        'https://www.reddit.com/r/GOONED/comments/1hvjy75/are_any_of_these_making_you_hard_would_love_to/', # multiple gifs & pics
        'https://www.reddit.com/r/DuaLipaGW/comments/1hql2b0/dua_lipa_squatting/', # reddit gif
        'https://www.reddit.com/r/WhaleTails/comments/1hv5kl9/my_husband_just_took_pics_instead_of_telling_me/', # image
        'https://www.reddit.com/r/DuaLipaGW/comments/1hqid7y/dua_lipa_ig_post/', # multiple images

        # DANBOORU 14-
        'https://danbooru.donmai.us/posts/8673626', #
        
        # BLUE SKY
        'https://bsky.app/profile/blueafterdark.bsky.social/post/3lf4aib4ic72b', # single
        'https://bsky.app/profile/goldy3d.bsky.social/post/3leykqg6qbc2f', # two images
        'https://bsky.app/profile/pervbrain.bsky.social/post/3lexyk5le6k24', # 3 images
        'https://bsky.app/profile/spring-bot.bsky.social/post/3lf4dkejxok2l', # video, tags
        
        # TIKTOK
        'https://www.tiktok.com/@generationofrationale/video/7445397898239495467',
        
        # RED GIFS
    ]
    filtered = [ u for u in TEST_URLS if 'bsky.app' in u ]
    return filtered
    

def test_bm():
    print('in test 2')
    
    bookmarks = BookmarksGetter()
    bookmarks = bookmarks.get_bookmarks('brave', 'Art')
    print(len(bookmarks))
    for b in bookmarks:
        print()
        for k, v in b.items():
            print('{:<20}: {}'.format(k, v))

""" TESTS END """










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
    
    elif args.show_logs:
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
        # urls_to_attempt = ...
        return
    
    elif args.bookmarks:
        print('[URLS] Retrieving urls from bookmarks ...')
        urls_to_attempt = get_urls_from_bookmarks(args, settings)
        
    elif args.use_test_urls:
        urls_to_attempt.extend(get_test_urls())
    
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
    for idx, url in enumerate(urls_to_attempt):
        command = get_gallerydl_command(url, dest, logins, skip=args.skip, extra_args=args.extra_args)
        if not (args.no_download and not args.down):
            print_url_download_info(idx, len(urls_to_attempt), url, len(succ), len(fail), times)
            start = time.time()
            result = subprocess.run(shlex.split(command), stdout=sys.stdout, stderr=sys.stderr, cwd=__SCRIPTDIR__)
            times.append(time.time() - start)
            print('Done. Took {:.1f}s. Returncode: {}'.format(times[-1], result.returncode))
            if result.returncode > 0:   fail.append(url)
            else:                       succ.append(url)
            log_download(result.returncode, url, idx)
        else:
            print('({}/{}) "{}"'.format(idx+1, len(urls_to_attempt), url))
            if args.show_command:print(command)
    
    return
    
# HELPER FUNCTIONS

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
    url = url.replace('https://', '')
    parts = url.split('/')
    for site in ['reddit', 'twitter', 'danbooru', 'tiktok', 'redgifs']:
        if site in parts[0]:
            return site
    return None
    
    #¤ https://x.com/home
    
    return usr, pss

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
    parser.add_argument('-show_logs', action='store_true',help='Prints out logs')

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
