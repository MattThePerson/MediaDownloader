


def main(post_id: str, user: str, service: str, media_path: str):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        'Accept': 'text/css',
    }
    
    api_call = f"https://kemono.cr/api/v1/{service}/user/{user}/post/{post_id}"
    api_call_comments = f"{api_call}/comments"
    
    res = requests.get(api_call, headers=headers)
    resc = requests.get(api_call_comments, headers=headers)

    if res.status_code != 200:
        print('ERROR: [scraping kemono api] bad response status code:', res.status_code)
        return

    if resc.status_code != 200:
        print('ERROR: [scraping kemono api] bad response status code:', res.status_code)
        return

    # 
    comments: list[str]
    data: dict
    try:
        data = res.json()
        comments = resc.json()
    except Exception as e:
        print(f"ERROR: [scraping kemono api] unable to convert api response to json:\nException={e}")
        return

    data["comments"] = comments
    print(f"found {len(comments)} comments")
    
    json_file = Path(media_path).parent / ".metadata" / f"{post_id}-api.json"
    json_file.parent.mkdir(exist_ok=True)
    # print('WRITING TO:', json_file)
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)



if __name__ == "__main__":
    import sys

    # exit if num > 1
    if int(sys.argv[1]) > 1:
        exit(0)

    # lazy imports
    import requests
    from pathlib import Path
    import json
    # from http.cookiejar import MozillaCookieJar

    # run main
    post_id = sys.argv[2]
    user = sys.argv[3]
    service = sys.argv[4]
    media_path = sys.argv[5]
    main(post_id, user, service, media_path)

