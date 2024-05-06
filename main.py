import os
import shutil
import glob
from mutagen.id3 import ID3, TPE2, TCMP
from mutagen.mp4 import MP4, MP4Tags
from typing import Final, Literal, Union
from logging import Logger
from LogController import get_logger

# ロガー
logger: Final[Logger] = get_logger(__name__)

# 各種定数
## ディレクトリのパスの区切り文字
DIRECTORY_PATH_DELIMITER: Final[str] = '\\'

## アルバムアーティストの暫定値、空文字のものをこの値に置き換える
VARIOUS_ALBUM_ARTIST: Final[str] = 'Various Artist'

# 読み込み対象のディレクトリ
SONG_DIRECTORY: Final[str] = 'songs'
TMP_DIRECTORY: Final[str] = 'tmp'
TMP_SONG_DIRECTORY: Final[str] = f'{TMP_DIRECTORY}{DIRECTORY_PATH_DELIMITER}{SONG_DIRECTORY}'

# tsv書き出し用
SONG_LIST_TSV_PATH_BEFORE: Final[str] = 'song_list_before.tsv'
SONG_LIST_TSV_PATH_AFTER: Final[str] = 'song_list_after.tsv'
TSV_HEADER: Final[list[str]] = [
    'file_path',
    'song_name',
    'artist_name',
    'album_name',
    'album_artist',
    'extension',
    'is_compilation'
]

class TsvInfo():
    """
    tsvファイルに入れる情報
    TSV_HEADERと合わせること
    """
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
            is_compilation: bool):
        self.file_path = file_path
        self.song_name = song_name
        self.artist_name = artist_name
        self.album_name = album_name
        self.album_artist = album_artist
        self.extension = extension
        self.is_compilation = is_compilation
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
    タグの書き換えはtmp内のファイルに対して行う
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
    with open(SONG_LIST_TSV_PATH_BEFORE, mode='w', encoding='utf_8_sig') as fp:
        fp.write(text)
        logger.info(f'Created TSV file: {SONG_LIST_TSV_PATH_BEFORE}')
    with open(SONG_LIST_TSV_PATH_AFTER, mode='w', encoding='utf_8_sig') as fp:
        fp.write(text)
        logger.info(f'Created TSV file: {SONG_LIST_TSV_PATH_AFTER}')
    return

def write_to_tsv(tsv_info: TsvInfo, filename: str) -> None:
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
    text += '\n'
    with open(filename, mode='a', encoding='utf_8_sig') as fp:
        fp.write(text)
    return

class SongController():
    """
    曲情報
    """
    file_info: FileInfo
    song_name: str
    artist_name: str
    album_name: str
    album_artist: str
    is_compilation: bool

    def __init__(self,
                file_info: FileInfo,
                song_name: str,
                artist_name: str,
                album_name: str,
                album_artist: str,
                is_compilation: bool,
                filename: Union[str, None]) -> None:
        self.file_info = file_info
        self.song_name = song_name
        self.artist_name = artist_name
        self.album_name = album_name
        self.album_artist = album_artist
        self.is_compilation = is_compilation
        tsv_info: TsvInfo = TsvInfo(
            file_path=file_info.file_path,
            song_name=self.song_name,
            artist_name=self.artist_name,
            album_name=self.album_name,
            album_artist=self.album_artist,
            extension=self.file_info.extension,
            is_compilation=self.is_compilation)
        if not filename == None:
            write_to_tsv(tsv_info, filename)
        return

    def get_artist(self) -> str:
        return self.artist_name

    def get_album_artist(self) -> str:
        return self.album_artist

    def get_compilation(self) -> bool:
        return self.is_compilation

class MP3Controller(SongController):
    """
    mp3ファイルの操作用
    """
    def __init__(self, file_info: FileInfo, tsv_filename: Union[str, None]) -> None:
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

        super().__init__(file_info,
                        song_name,
                        artist_name,
                        album_name,
                        album_artist,
                        is_compilation,
                        tsv_filename)
        return

class M4AController(SongController):
    """
    m4aファイルの操作用
    iTunesで作ったAACとALACが取り扱える
    """
    def __init__(self, file_info: FileInfo, tsv_filename: Union[str, None]) -> None:
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

        super().__init__(file_info,
                        song_name,
                        artist_name,
                        album_name,
                        album_artist,
                        is_compilation,
                        tsv_filename)
        return

def get_directory_path(file_path: str) -> tuple[str, str]:
    """
    ファイルのパスを入力して、ディレクトリのパスとファイル名を返す
    """
    path: list[str] = file_path.split(DIRECTORY_PATH_DELIMITER)
    directory: str = DIRECTORY_PATH_DELIMITER.join(path[:-1])
    filename: str = path[-1]
    return directory, filename

def change_tags_in_same_dirs(dir_name: str, is_change_album_artist: bool, is_change_compilation: bool):
    """
    タグの書き換え
    """
    file_info_list: list[FileInfo] = create_file_info_list(dir_name)
    for file_info in file_info_list:
        if file_info.extension == 'mp3':
            mp3_info: ID3 = ID3(file_info.file_path)
            if is_change_album_artist:
                mp3_info.add(TPE2(encoding=3, text=VARIOUS_ALBUM_ARTIST))
            if is_change_compilation:
                mp3_info.add(TCMP(encoding=3, text="1"))
            mp3_info.save()
            logger.info(f'Change tags: {file_info.file_path}')
        elif file_info.extension == 'm4a':
            # AAC or ALAC
            mp4_info: MP4 = MP4(file_info.file_path)
            if is_change_album_artist:
                mp4_info['aART'] = VARIOUS_ALBUM_ARTIST
            if is_change_compilation:
                mp4_info['cpil'] = True
            mp4_info.save()
            logger.info(f'Change tags: {file_info.file_path}')
        else:
            continue

def create_file_info_list(dir_path: str) -> list[FileInfo]:
    """
    ファイル一覧の作成
    """
    # エスケープしないと[Disc 1]などがディレクトリ名に含まれているときに読み込めない
    _dir_path = glob.escape(dir_path)

    file_info_list: list[FileInfo]= []
    for _file_path in glob.glob(f'{_dir_path}/**/*.*', recursive=True):
        # スラッシュをバックスラッシュに置き換えて区切り文字を統一
        file_path: str = _file_path.replace('/', DIRECTORY_PATH_DELIMITER)
        extension: str = file_path.split('.')[-1]
        info: FileInfo = FileInfo(
            file_path=file_path,
            extension=extension
        )
        file_info_list.append(info)
    return file_info_list

def main() -> None:
    """
    メインの処理
    """
    # TMP_SONG_DIRECTORYディレクトリ以下のファイルパスと拡張子の取得
    file_info_list: list[FileInfo] = create_file_info_list(TMP_SONG_DIRECTORY)

    # 処理前の結果をtsvに書き出す
    for file_info in file_info_list:
        if file_info.extension == 'mp3':
            controller: MP3Controller = MP3Controller(file_info, SONG_LIST_TSV_PATH_BEFORE)
        elif file_info.extension == 'm4a':
            controller: M4AController = M4AController(file_info, SONG_LIST_TSV_PATH_BEFORE)
        else:
            continue

    # 同じディレクトリ内に異なるアーティストがあるときに、
    # コンピレーションアルバムとしてフラグを立てる
    # アルバムアーティストが空文字だった場合VARIOUS_ALBUM_ARTISTの値に置き換える
    current_directory_path: str = ''
    before_directory_path: str = ''
    current_artist_name: str = ''
    before_artist_name: str = ''
    for file_info in file_info_list:
        current_directory_path, current_filename = get_directory_path(file_info.file_path)
        if file_info.extension == 'mp3':
            controller: MP3Controller = MP3Controller(file_info, None)
        elif file_info.extension == 'm4a':
            controller: M4AController = M4AController(file_info, None)
        else:
            continue
        current_artist_name = controller.get_artist()

        # input()
        print('---------------')
        print(f'Current directory: {current_directory_path}')
        print(f'Current filename: {current_filename}')
        print(f'Before Dir path: {before_directory_path}')
        print(f'Current Dir path: {current_directory_path}')
        print(f'Before artist: {before_artist_name}')
        print(f'Current artist: {current_artist_name}')

        if before_directory_path == '':
            # 1周目のみ、変数を初期化して次の曲へ進む
            before_directory_path = current_directory_path
            before_artist_name = current_artist_name
            continue

        if before_directory_path != current_directory_path:
            # 次のディレクトリに移った時
            # 変数の初期化＆処理済みディレクトリフラグをFalseにして次の曲へ進む
            before_directory_path = current_directory_path
            before_artist_name = current_artist_name
            continue

        if before_directory_path == current_directory_path:
            """
            ●同じディレクトリ内のファイルのとき
            1つ前の曲と現在の曲のアーティスト名を比較する
            ・異なっていた場合：
                - アルバムアーティストが空欄でコンピレーション
                    ARIOUS_ALBUM_ARTISTをアルバムアーティストに設定する
                - アルバムアーティストが空欄でコンピレーションではない
                    ARIOUS_ALBUM_ARTISTをアルバムアーティストに設定し、コンピレーションのフラグを立てる
                - アルバムアーティストが設定済みで、かつコンピレーション
                    何もせず次の曲へ進む
                - アルバムアーティストが設定済みだがコンピレーションではない
                    コンピレーションのフラグを立てる
            ・同じ場合：
                何もせず次の曲へ進む
            """
            if before_artist_name != current_artist_name:
                album_artist = controller.get_album_artist()
                is_compilation = controller.get_compilation()
                print(f'> Album artist: {album_artist} (len: {len(album_artist)})')
                print(f'> Compilation: {is_compilation}')
                if album_artist == '' and is_compilation == True:
                    change_tags_in_same_dirs(current_directory_path, True, False)
                elif album_artist == '' and is_compilation == False:
                    change_tags_in_same_dirs(current_directory_path, True, True)
                elif album_artist != '' and is_compilation == True:
                    pass
                elif album_artist != '' and is_compilation == False:
                    change_tags_in_same_dirs(current_directory_path, False, True)
            before_directory_path = current_directory_path
            before_artist_name = current_artist_name
            continue

    # 処理結果をafterのtsvに書き出す
    for file_info in file_info_list:
        if file_info.extension == 'mp3':
            controller: MP3Controller = MP3Controller(file_info, SONG_LIST_TSV_PATH_AFTER)
        elif file_info.extension == 'm4a':
            controller: M4AController = M4AController(file_info, SONG_LIST_TSV_PATH_AFTER)
        else:
            continue
    return

if __name__ == '__main__':
    init_dirs()
    init_tsv()
    main()
