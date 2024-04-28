import glob
from mutagen.id3 import ID3
from mutagen.mp4 import MP4
from typing import Final

# 読み込み対象のディレクトリ
DIRECTORY: Final[str] = 'songs'

class FileInfo:
    """
    ファイルの情報
    """
    file_path: str
    extension: str

    def __init__(self, file_path: str, extension: str) -> None:
        self.file_path = file_path
        self.extension = extension

def main() -> None:
    """
    メインの処理
    """
    # DIRECTORYディレクトリ以下のファイルパスと拡張子の取得
    file_info_list: list[FileInfo]= []
    for file_path in glob.glob(f'{DIRECTORY}/*.*', recursive=True):
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
    main()
