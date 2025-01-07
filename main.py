import subprocess
import shlex
import sys
import os
import argparse

""" 
TODO:
# Reddit
- convert m4v to mp4

# Twitter
- add username and password passing as arguments (remove from config)

"""

def testing(args):
    print("Hey there!")

    TEST_URLS = [
        'https://x.com/emiillb/stadqdbnqiqywtus/1876360999751860691',
        'https://www.reddit.com/r/LenaPaul/comments/1hv9c96/lena_riding/',
        'https://www.tiktok.com/@generationofrationale/video/7445397898239495467',
        'https://x.com/EroticNansensu/status/1876358077525770543',
    ]
    url = TEST_URLS[3]
    command = 'venv/bin/gallery-dl --config .config/gallery-dl.conf "{}"'.format(url)
    # print(command)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    result = subprocess.run(shlex.split(command), stdout=sys.stdout, stderr=sys.stderr, cwd=script_dir)
    print('returncode:', result.returncode)



if __name__ == '__main__':
    parser = argparse.ArgumentParser("Wrapper utility for gallery-dl")
    
    parser.add_argument('-gallery', action='store_true', help='Show -h screen for gallery-dl')
    parser.add_argument('-settings', action='store_true', help='Print out settings')

    parser.add_argument('-b', '--bookmarks', action='store_true', help='Get urls from bookmarks')
    parser.add_argument('-r', '--read-file', help='Pass file to read urls from')
    
    parser.add_argument('-site', help='Limit urls to site')
    # parser.add_argument('-user', help='Scrape ')
    
    parser.add_argument('-limit', help='Limit for how many urls to handle')
    # parser.add_argument('-', help='')
    
    print()
    testing(parser.parse_args())
    print()
