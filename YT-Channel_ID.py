from googleapiclient.discovery import build
import re
import urllib.parse
import pyperclip
from colorama import Fore, Style, init
import time
import sys
import itertools
import threading

# YouTube Data APIのAPIキーを設定
API_KEY = 'YOU_API_KEY'

# スピナーアニメーションを行う関数
def animate():
    for c in itertools.cycle(['|', '/', '-', '\\']):
        if done:
            break
        sys.stdout.write('\r' + Fore.LIGHTWHITE_EX + 'チャンネルIDを取得しています ' + c)
        sys.stdout.flush()
        time.sleep(0.1)

def get_channel_id_from_url(url):
    # @形式と通常のチャンネル名の両方に対応
    match = re.search(r'(?:https?://)?(?:www\.)?(?:youtube\.com/(?:channel|c|user)/|youtu\.be/|youtube\.com/@)([^/?]+)', url)
    if match:
        # チャンネル名をデコード
        channel_name = urllib.parse.unquote(match.group(1))
        return get_channel_id(channel_name)
    else:
        return ""
        return "無効なURLです。"

def get_channel_id(channel_name):
    youtube = build('youtube', 'v3', developerKey=API_KEY)

    # チャンネル情報を取得
    request = youtube.channels().list(
        part='id',
        forUsername=channel_name
    )

    response = request.execute()

    if 'items' in response and len(response['items']) > 0:
        return response['items'][0]['id']
    else:
        # カスタムURLの場合は別の方法で取得
        request = youtube.search().list(
            q=channel_name,
            type='channel',
            part='id'
        )
        response = request.execute()

        if 'items' in response and len(response['items']) > 0:
            return response['items'][0]['id']
        else:
            return "チャンネルIDが見つかりませんでした。"

# チャンネルURLを入力
channel_url = input("YouTubeチャンネルのURLを入力してください: ")
channel_id = get_channel_id_from_url(channel_url)

# Coloramaの初期化
init(autoreset=True)

# スピナーアニメーションを別スレッドで開始
done = False
t = threading.Thread(target=animate)
t.start()

# ここで実際の処理を行う（例として3秒待つ）
time.sleep(3)  # 実際のAPIコールの処理に置き換える

# チャンネルIDの取得が完了したらスピナーを止める
done = True
t.join()

# チャンネルIDのみを表示
if channel_id and "無効なURL" not in channel_id:
    print("\n" + Fore.LIGHTGREEN_EX + "チャンネルIDが取得できました")

    time.sleep(1)  # 1秒待つ
    print(Fore.LIGHTWHITE_EX + "チャンネルIDは " + Fore.LIGHTYELLOW_EX + channel_id['channelId'] + Fore.LIGHTWHITE_EX + " です")

    time.sleep(2)  # 2秒待つ
    print("")
    copy = input(Fore.LIGHTWHITE_EX + "チャンネルIDをクリップボードにコピーしますか？ (・・?  (y/n): ")

    if copy.lower() == 'y':
        print("")
        pyperclip.copy(channel_id['channelId'])
        print(Fore.LIGHTWHITE_EX + "チャンネルIDをクリップボードにコピーしました")
        time.sleep(1)  # 確認のために1秒待つ
        print("")
        print(Fore.LIGHTGREEN_EX + "コピーが完了しました！まもなくウィンドウが閉じます")
    else:
        print("")
        print(Fore.LIGHTGREEN_EX + "まもなくウィンドウが閉じます")
else:
    print(Fore.RED + channel_id)
    print(Fore.LIGHTRED_EX + "URLが正しくないためチャンネルIDを取得できませんでした")
