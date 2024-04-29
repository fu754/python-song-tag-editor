import os
import shutil
import glob
from mutagen.id3 import ID3
from mutagen.mp4 import MP4, MP4Tags
from typing import Final, Literal

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
    'extension',
    'is_compilation',
    'id3_version'
]

class TsvInfo():
    file_path: str
    song_name: str
    artist_name: str
    album_name: str
    album_artist: str
    extension: str
    is_compilation: bool
    id3_version: int

    def __init__(self,
            file_path: str,
            song_name: str,
            artist_name: str,
            album_name: str,
            album_artist: str,
            extension: str,
            is_compilation: bool,
            id3_version: int):
        self.file_path = file_path
        self.song_name = song_name
        self.artist_name = artist_name
        self.album_name = album_name
        self.album_artist = album_artist
        self.extension = extension
        self.is_compilation = is_compilation
        self.id3_version = id3_version
        return

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

def write_to_tsv(tsv_info: TsvInfo) -> None:
    text: str = ''
    text += f'{tsv_info.file_path}\t'
    text += f'{tsv_info.song_name}\t'
    text += f'{tsv_info.artist_name}\t'
    text += f'{tsv_info.album_name}\t'
    text += f'{tsv_info.album_artist}\t'
    text += f'{tsv_info.extension}\t'
    text += f'{tsv_info.is_compilation}\t'
    text += f'{tsv_info.id3_version}'
    text += '\n'
    with open(SONG_LIST_TSV_PATH, mode='a', encoding='utf_8_sig') as fp:
        fp.write(text)
    return

def mp3_controller(file_info: FileInfo) -> None:
    mp3_info: ID3 = ID3(file_info.file_path)
    print(mp3_info.pprint())
    song_name: str      = mp3_info['TIT2'].text[0]
    artist_name: str    = mp3_info['TPE1'].text[0]
    album_name: str     = mp3_info['TALB'].text[0]
    # アルバムアーティストが設定されているか確認、なければ空文字
    if 'TPE2' in mp3_info:
        album_artist: str   = mp3_info['TPE2'].text[0]
    else:
        album_artist: str = ''

    # コンピレーションアルバムかどうかのフラグの取得
    is_compilation: bool
    if 'TCMP' in mp3_info:
        _is_compilation: Literal["0", "1"] = mp3_info['TCMP']
        if _is_compilation == "0":
            is_compilation: False
        elif _is_compilation == "1":
            is_compilation = True
        else:
            raise Exception(f'TCMP value: {_is_compilation}')
    else:
        is_compilation = False

    version = mp3_info.version[0]

    # tsvに書き出し
    tsv_info: TsvInfo = TsvInfo(
        file_path=file_info.file_path,
        song_name=song_name,
        artist_name=artist_name,
        album_name=album_name,
        album_artist=album_artist,
        extension=file_info.extension,
        is_compilation=is_compilation,
        id3_version=version
    )
    write_to_tsv(tsv_info)
    return

def m4a_controller(file_info: FileInfo) -> None:
    mp4_info: MP4 = MP4(file_info.file_path)
    print(mp4_info.pprint())
    tag: MP4Tags = mp4_info.tags
    song_name: str      = tag['\xa9nam'][0]
    artist_name: str    = tag['\xa9ART'][0]
    album_name: str     = tag['\xa9alb'][0]

    # アルバムアーティストが設定されているか確認、なければ空文字
    if 'aART' in tag:
        album_artist: str   = tag['aART'][0]
    else:
        album_artist: str   = ''

    # コンピレーションアルバムかどうかのフラグの取得
    is_compilation: bool = tag['cpil']

    # tsvに書き出し
    tsv_info: TsvInfo = TsvInfo(
        file_path=file_info.file_path,
        song_name=song_name,
        artist_name=artist_name,
        album_name=album_name,
        album_artist=album_artist,
        extension=file_info.extension,
        is_compilation=is_compilation,
        id3_version=-1
    )
    write_to_tsv(tsv_info)
    return

def main() -> None:
    """
    メインの処理
    """
    # TMP_SONG_DIRECTORYディレクトリ以下のファイルパスと拡張子の取得
    file_info_list: list[FileInfo]= []
    for file_path in glob.glob(f'{TMP_SONG_DIRECTORY}/**/*.*', recursive=True):
        extension: str = file_path.split('.')[-1]
        info: FileInfo = FileInfo(
            file_path=file_path,
            extension=extension
        )
        file_info_list.append(info)

    # タグの取得
    for file_info in file_info_list:
        print(f'-------- Current file: {file_info.file_path}')
        if file_info.extension == 'mp3':
            mp3_controller(file_info)
        elif file_info.extension == 'm4a':
            m4a_controller(file_info)
        else:
            pass
    return

if __name__ == '__main__':
    # init_dirs()
    init_tsv()
    main()
