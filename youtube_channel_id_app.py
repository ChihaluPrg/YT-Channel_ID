import sys
import re
import urllib.parse
import pyperclip
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QDialog, QDialogButtonBox
from PyQt5.QtCore import QThread, pyqtSignal, QSettings, QPoint
from googleapiclient.discovery import build

API_KEY = 'YOUR_API_KEY'

class ChannelIDWorker(QThread):
    result_ready = pyqtSignal(dict)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        channel_info = get_channel_id_from_url(self.url)
        self.result_ready.emit(channel_info)

def get_channel_id_from_url(url):
    match = re.search(r'(?:https?://)?(?:www\.)?(?:youtube\.com/(?:channel|c|user)/|youtu\.be/|youtube\.com/@)([^/?]+)', url)
    if match:
        channel_name = urllib.parse.unquote(match.group(1))
        return get_channel_id(channel_name)
    else:
        return {"error": "無効なURLです。"}

def get_channel_id(channel_name):
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    request = youtube.channels().list(
        part='id',
        forUsername=channel_name
    )
    response = request.execute()

    if 'items' in response and len(response['items']) > 0:
        return {"channelId": response['items'][0]['id']}
    else:
        request = youtube.search().list(
            q=channel_name,
            type='channel',
            part='id'
        )
        response = request.execute()

        if 'items' in response and len(response['items']) > 0:
            return {"channelId": response['items'][0]['id']}
        else:
            return {"error": "チャンネルIDが見つかりませんでした。"}

class YouTubeChannelIDApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("icon.ico"))
        self.settings = QSettings("MyCompany", "YouTubeChannelIDApp")  # ウィンドウ位置を保存するための設定
        self.popup_position = QPoint(100, 100)  # ポップアップの初期位置
        self.init_ui()
        self.load_settings()  # 前回の位置を読み込む

    def init_ui(self):
        self.setWindowTitle('YouTubeチャンネルID取得ツール')

        layout = QVBoxLayout()

        self.label_url = QLabel('YouTubeチャンネルのURLを入力してください:')
        self.label_url.setStyleSheet("font-size: 16px; letter-spacing: 2px; margin-bottom: 15px; margin-top: 15px;")

        self.entry_url = QLineEdit(self)
        self.entry_url.setPlaceholderText("URLをここに入力")
        self.entry_url.setStyleSheet("font-size: 14px; padding: 10px; margin-bottom: 10px;")

        self.button_start = QPushButton('チャンネルIDを取得', self)
        self.button_start.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                font-size: 16px;
                border-radius: 5px;
                letter-spacing: 2px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.button_start.clicked.connect(self.start_process)

        layout.addWidget(self.label_url)
        layout.addWidget(self.entry_url)
        layout.addWidget(self.button_start)

        self.setLayout(layout)

    def start_process(self):
        url = self.entry_url.text()
        if not url:
            QMessageBox.critical(self, "エラー", "URLを入力してください")
            return

        # 別スレッドで実行
        self.worker = ChannelIDWorker(url)
        self.worker.result_ready.connect(self.display_result)
        self.worker.start()

    def display_result(self, channel_info):
        if 'error' in channel_info:
            QMessageBox.critical(self, "エラー", channel_info['error'])
        else:
            channel_id = channel_info['channelId']
            self.show_popup(channel_id)

    def show_popup(self, channel_id):
        # ポップアップダイアログを作成
        dialog = QDialog(self)
        dialog.setWindowTitle("チャンネルID取得結果")

        # メインウィンドウの位置とサイズを取得
        main_window_rect = self.geometry()
        dialog_width = 300
        dialog_height = 150

        # ポップアップの位置を計算（メインウィンドウの上）
        dialog_x = main_window_rect.x() + (main_window_rect.width() - dialog_width- 90) // 2
        dialog_y = main_window_rect.y() - dialog_height - -110  # メインウィンドウの上に少し余裕を持たせる

        dialog.setGeometry(dialog_x, dialog_y, dialog_width, dialog_height)

        layout = QVBoxLayout()

        # 結果表示ラベル
        label = QLabel(f"チャンネルIDは: " + channel_id['channelId'] + " です")
        label.setStyleSheet("font-size: 16px; margin: 10px; letter-spacing: 2px;")
        layout.addWidget(label)

        # コピー用のボタンを追加
        copy_button = QPushButton('クリップボードにコピー', dialog)
        copy_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                font-size: 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        copy_button.clicked.connect(lambda: self.copy_to_clipboard(channel_id))
        layout.addWidget(copy_button)

        # OKボタン
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.setStyleSheet("QDialogButtonBox { margin: 10px; }")
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)

        dialog.setLayout(layout)

        # ポップアップの位置を保存
        dialog.finished.connect(lambda: self.save_popup_position(dialog))

        dialog.exec_()

    def save_popup_position(self, dialog):
        # ダイアログが閉じられたときの位置を保存
        self.popup_position = dialog.x(), dialog.y()

    def copy_to_clipboard(self, text):
        pyperclip.copy(text)
        QMessageBox.information(self, "コピー完了", "チャンネルIDをクリップボードにコピーしました")

    def closeEvent(self, event):
        self.save_settings()  # ウィンドウ位置を保存
        super().closeEvent(event)

    def save_settings(self):
        # 現在のウィンドウ位置とサイズを保存
        self.settings.setValue("pos", self.pos())

    def load_settings(self):
        # 前回保存された位置があれば、その位置にウィンドウを配置
        pos = self.settings.value("pos", QPoint(100, 100))
        self.move(pos)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = YouTubeChannelIDApp()
    window.show()
    sys.exit(app.exec_())
