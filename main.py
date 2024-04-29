import os
import shutil
import glob
from mutagen.id3 import ID3
from mutagen.mp4 import MP4
from typing import Final

# 読み込み対象のディレクトリ
SONG_DIRECTORY: Final[str] = 'songs'
TMP_DIRECTORY: Final[str] = 'tmp'
TMP_SONG_DIRECTORY: Final[str] = f'{TMP_DIRECTORY}/{SONG_DIRECTORY}'

class FileInfo:
    """
    ファイルの情報
    """
    file_path: str
    extension: str

    def __init__(self, file_path: str, extension: str) -> None:
        self.file_path = file_path
        self.extension = extension

def init_dirs() -> None:
    if os.path.exists(TMP_DIRECTORY):
        shutil.rmtree(TMP_DIRECTORY)
    os.makedirs(TMP_DIRECTORY)
    for file_path in glob.glob(f'{SONG_DIRECTORY}/**/*.*', recursive=True):
        destination_dir: str = os.path.join(TMP_DIRECTORY, os.path.dirname(file_path))
        destination_file_path: str = os.path.join(TMP_DIRECTORY, file_path)
        os.makedirs(destination_dir, exist_ok=True)
        shutil.copy(file_path, destination_file_path)
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
            tags = ID3(file_info.file_path)
            print(tags.pprint())
        if file_info.extension == 'm4a':
            tags = MP4(file_info.file_path)
            print(tags.pprint())
    return

if __name__ == '__main__':
    init_dirs()
    main()
