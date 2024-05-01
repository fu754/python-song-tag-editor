import os
import shutil
import glob
from mutagen.id3 import ID3
from mutagen.mp4 import MP4, MP4Tags
from typing import Final, Literal
from logging import Logger
from LogController import get_logger

logger: Final[Logger] = get_logger(__name__)

# 各種定数
DIRECTORY_PATH_DELIMITER: Final[str] = '\\'

# 読み込み対象のディレクトリ
SONG_DIRECTORY: Final[str] = 'songs'
TMP_DIRECTORY: Final[str] = 'tmp'
TMP_SONG_DIRECTORY: Final[str] = f'{TMP_DIRECTORY}{DIRECTORY_PATH_DELIMITER}{SONG_DIRECTORY}'

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
        logger.info(f'Delete directory: {TMP_DIRECTORY}')
        shutil.rmtree(TMP_DIRECTORY)
    os.makedirs(TMP_DIRECTORY)
    logger.info(f'Created directory: {TMP_DIRECTORY}')
    for file_path in glob.glob(f'{SONG_DIRECTORY}/**/*.*', recursive=True):
        destination_dir: str = os.path.join(TMP_DIRECTORY, os.path.dirname(file_path))
        destination_file_path: str = os.path.join(TMP_DIRECTORY, file_path)
        os.makedirs(destination_dir, exist_ok=True)
        shutil.copy(file_path, destination_file_path)
        logger.info(f'Copied: {file_path} -> {destination_file_path}')
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
    logger.info(f'Created TSV file: {SONG_LIST_TSV_PATH}')
    return

def write_to_tsv(tsv_info: TsvInfo) -> None:
    """
    tsvに曲情報を書き出す
    """
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

class SongController():
    file_info: FileInfo
    song_name: str
    artist_name: str
    album_name: str
    album_artist: str
    is_compilation: bool
    version: int

    def __init__(self,
                file_info: FileInfo,
                song_name: str,
                artist_name: str,
                album_name: str,
                album_artist: str,
                is_compilation: bool,
                version: int) -> None:
        self.file_info = file_info
        self.song_name = song_name
        self.artist_name = artist_name
        self.album_name = album_name
        self.album_artist = album_artist
        self.is_compilation = is_compilation
        self.version = version
        tsv_info: TsvInfo = TsvInfo(
            file_path=file_info.file_path,
            song_name=self.song_name,
            artist_name=self.artist_name,
            album_name=self.album_name,
            album_artist=self.album_artist,
            extension=self.file_info.extension,
            is_compilation=self.is_compilation,
            id3_version=-1
        )
        write_to_tsv(tsv_info)
        return

    def get_artist(self) -> str:
        return self.artist_name

class MP3Controller(SongController):
    """
    mp3ファイルの操作用
    """
    def __init__(self, file_info: FileInfo) -> None:
        mp3_info: ID3 = ID3(file_info.file_path)
        song_name: str      = mp3_info['TIT2'].text[0]
        artist_name: str    = mp3_info['TPE1'].text[0]
        album_name: str     = mp3_info['TALB'].text[0]
        # アルバムアーティストが設定されているか確認、なければ空文字
        if 'TPE2' in mp3_info:
            album_artist   = mp3_info['TPE2'].text[0]
        else:
            album_artist = ''
        # コンピレーションアルバムかどうかのフラグの取得
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

        # ID3のバージョンを取得
        version = mp3_info.version[0]

        super().__init__(file_info,
                        song_name,
                        artist_name,
                        album_name,
                        album_artist,
                        is_compilation,
                        version)
        return

class M4AController(SongController):
    """
    m4aファイルの操作用
    AACとALACが取り扱える
    """
    def __init__(self, file_info: FileInfo) -> None:
        mp4_info: MP4 = MP4(file_info.file_path)
        tag: MP4Tags = mp4_info.tags
        song_name: str      = tag['\xa9nam'][0]
        artist_name: str    = tag['\xa9ART'][0]
        album_name: str     = tag['\xa9alb'][0]
        # アルバムアーティストが設定されているか確認、なければ空文字
        if 'aART' in tag:
            album_artist = tag['aART'][0]
        else:
            album_artist = ''

        # コンピレーションアルバムかどうかのフラグの取得
        is_compilation: bool = tag['cpil']
        version = -1

        super().__init__(file_info,
                        song_name,
                        artist_name,
                        album_name,
                        album_artist,
                        is_compilation,
                        version)
        return

def get_directory_path(file_path: str) -> tuple[str, str]:
    """
    ファイルのパスを入力して、ディレクトリのパスとファイル名を返す
    """
    path: list[str] = file_path.split(DIRECTORY_PATH_DELIMITER)
    directory: str = DIRECTORY_PATH_DELIMITER.join(path[:-1])
    filename: str = path[-1]
    return directory, filename

def main() -> None:
    """
    メインの処理
    """
    # TMP_SONG_DIRECTORYディレクトリ以下のファイルパスと拡張子の取得
    file_info_list: list[FileInfo]= []
    for _file_path in glob.glob(f'{TMP_SONG_DIRECTORY}/**/*.*', recursive=True):
        # スラッシュをバックスラッシュに置き換えて区切り文字を統一
        file_path: str = _file_path.replace('/', DIRECTORY_PATH_DELIMITER)
        extension: str = file_path.split('.')[-1]
        info: FileInfo = FileInfo(
            file_path=file_path,
            extension=extension
        )
        file_info_list.append(info)

    # 同じディレクトリ内に異なるアーティストがあるときに、
    # コンピレーションアルバムとしてフラグを立てる
    current_directory_path: str = ''
    current_artist_name: str = ''
    for file_info in file_info_list:
        current_directory_path, current_filename = get_directory_path(file_info.file_path)
        print(f'-------- Current directory: {current_directory_path}')
        print(f'-------- Current filename: {current_filename}')
        if file_info.extension == 'mp3':
            controller: MP3Controller = MP3Controller(file_info)
        elif file_info.extension == 'm4a':
            # AAC or ALAC
            controller: M4AController = M4AController(file_info)
        else:
            continue
        current_artist_name = controller.get_artist()
    return

if __name__ == '__main__':
    # init_dirs()
    init_tsv()
    main()
