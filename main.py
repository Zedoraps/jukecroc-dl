import time

import requests as requests
import youtube_dl
import argparse

uri = "https://croc.moes.li/api/collections"


def get_token(user, password):
    print("Trying to aqcuire token for user", user)
    auth = requests.post(uri + "/users/auth-with-password", {
        "identity": user,
        "password": password
    })

    if (auth.ok):
        print("acquired token")
        return auth.json()["token"]
    else:
        print("ERROR: Auth request failed", auth, auth.json())
        raise Exception("unable to get token")


def get_videos(token):
    print("loading videos")
    videos = requests.get(uri + "/videos/records", headers={'Content-Type': 'application/json',
                                                            'Authorization': 'Bearer {}'.format(token)},
                          params={
                              "perPage": "500",
                              "filter": "(added = False)"
                          })

    if videos.ok:
        print(f"found {videos.json()['totalItems']} songs")
        return videos.json()
    else:
        print("ERROR: Search request failed", videos, videos.json())
        raise Exception("Failed to load the videos", videos, videos.json())


def has_enough_likes(id, token):
    likes = requests.get(uri + "/likes/records", headers={'Content-Type': 'application/json',
                                                          'Authorization': 'Bearer {}'.format(token)},
                         params={
                             "perPage": "500",
                             "filter": 'video="' + id + '"'
                         })

    if (likes.ok):
        return likes.json()["totalItems"] >= 5
    else:
        raise Exception("Failed to load the likes for the video", id, likes, likes.json())


def mark_video_as_added(token, video):
    updateResult = requests.patch(uri + "/videos/records/" + video["id"], json={"added": "true"},
                                  headers={'Content-Type': 'application/json',
                                           'Authorization': 'Bearer {}'.format(token)}, )
    print(updateResult, updateResult.json())


def download_song(exportDir, videosToDownload, token):
    for video in videosToDownload:
        print("starting to download:", video)
        ydl_opts = {
            "outtmpl": exportDir + video["title"].replace(" ", "_") + ".%(ext)s",
            "cachedir": False,
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            }],
        }
        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video["uri"]])
        except:
            print(f"Failed to download {video['title']}")
            break
        mark_video_as_added(token, video)


def run(user, password, output):
    videosToDownload = []

    token = get_token(user, password)
    videos = get_videos(token)

    for i in videos["items"]:
        print(f"checking video={i['title']}"),
        if has_enough_likes(i["id"], token):
            print("Adding song:" + i["uri"], i["title"])
            videosToDownload.append({
                "title": i["title"],
                "uri": i["uri"],
                "id": i["id"],
                "starttime": i["starttime"],
            })

    download_song(output, videosToDownload, token)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    argParser = argparse.ArgumentParser()
    argParser.add_argument("-u", "--user", help="Pocketbase username")
    argParser.add_argument("-p", "--password", help="Pocketbase password")
    argParser.add_argument("-o", "--output", help="Output directory")

    args = argParser.parse_args()
    print("args=%s" % args)
    run(args.user, args.password, args.output)
