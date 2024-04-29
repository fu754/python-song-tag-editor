import os
import shutil
import glob
from mutagen.id3 import ID3, ID3Tags
from mutagen.mp4 import MP4, MP4Tags
from typing import Final

# 読み込み対象のディレクトリ
SONG_DIRECTORY: Final[str] = 'songs'
TMP_DIRECTORY: Final[str] = 'tmp'
TMP_SONG_DIRECTORY: Final[str] = f'{TMP_DIRECTORY}/{SONG_DIRECTORY}'

# tsv書き出し用
SONG_LIST_TSV_PATH: Final[str] = 'song_list.tsv'
TSV_HEADER: Final[list[str]] = [
    'file_path',
    'song_name',
    'artist_name',
    'album_name',
    'album_artist',
    'extension'
]

class FileInfo():
    """
    ファイルの情報
    """
    file_path: str
    extension: str

    def __init__(self, file_path: str, extension: str) -> None:
        self.file_path = file_path
        self.extension = extension

def init_dirs() -> None:
    """
    ディレクトリの初期化
    songsディレクトリ以下のファイルをすべてtmpにコピーする
    """
    if os.path.exists(TMP_DIRECTORY):
        shutil.rmtree(TMP_DIRECTORY)
    os.makedirs(TMP_DIRECTORY)
    for file_path in glob.glob(f'{SONG_DIRECTORY}/**/*.*', recursive=True):
        destination_dir: str = os.path.join(TMP_DIRECTORY, os.path.dirname(file_path))
        destination_file_path: str = os.path.join(TMP_DIRECTORY, file_path)
        os.makedirs(destination_dir, exist_ok=True)
        shutil.copy(file_path, destination_file_path)
    return

def init_tsv() -> None:
    """
    song_list.tsvの初期化
    """
    text: str = ''
    for h in TSV_HEADER:
        text += f'{h}\t'
    # 末尾のタブを削除
    text = text.rstrip('\t')
    text += '\n'
    with open(SONG_LIST_TSV_PATH, mode='w', encoding='utf_8_sig') as fp:
        fp.write(text)
    return

def main() -> None:
    """
    メインの処理
    """
    # DIRECTORYディレクトリ以下のファイルパスと拡張子の取得
    file_info_list: list[FileInfo]= []
    for file_path in glob.glob(f'{TMP_SONG_DIRECTORY}/**/*.*', recursive=True):
        extension: str = file_path.split('.')[-1]
        info: FileInfo = FileInfo(
            file_path=file_path,
            extension=extension
        )
        file_info_list.append(info)

    # タグの表示
    for file_info in file_info_list:
        print(f'-------- Current file: {file_info.file_path}')
        if file_info.extension == 'mp3':
            mp3_info: ID3 = ID3(file_info.file_path)
            # print(mp3_info.pprint())
            song_name: str      = mp3_info['TIT2'].text[0]
            artist_name: str    = mp3_info['TPE1'].text[0]
            album_name: str     = mp3_info['TALB'].text[0]
            # アルバムアーティストが設定されているか確認、なければ空文字
            if 'TPE2' in mp3_info:
                album_artist: str   = mp3_info['TPE2'].text[0]
            else:
                album_artist: str = ''
            with open(SONG_LIST_TSV_PATH, mode='a', encoding='utf_8_sig') as fp:
                text: str = f'{file_info.file_path}\t{song_name}\t{artist_name}\t{album_name}\t{album_artist}\t{file_info.extension}\n'
                fp.write(text)
        elif file_info.extension == 'm4a':
            mp4_info: MP4 = MP4(file_info.file_path)
            # print(mp4_info.pprint())
            tag: MP4Tags = mp4_info.tags
            song_name: str      = tag['\xa9nam'][0]
            artist_name: str    = tag['\xa9ART'][0]
            album_name: str     = tag['\xa9alb'][0]
            album_artist: str   = tag['aART'][0]
            with open(SONG_LIST_TSV_PATH, mode='a', encoding='utf_8_sig') as fp:
                text: str = f'{file_info.file_path}\t{song_name}\t{artist_name}\t{album_name}\t{album_artist}\t{file_info.extension}\n'
                fp.write(text)
        else:
            pass
    return

if __name__ == '__main__':
    init_dirs()
    init_tsv()
    main()
