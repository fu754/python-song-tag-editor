# 自分用：楽曲ファイルのタグ情報の一括編集スクリプト
## 何ができるか
- 同じディレクトリ内で複数アーティストが存在したときにコンピレーションアルバムのフラグを有効にする
    - 上記の条件を満たす場合にアルバムアーティストが設定されていなかった場合に`VARIOUS_ALBUM_ARTIST: Final[str] = 'Various Artist'`へ文字列置換を行う

## 使い方
1. `songs`ディレクトリにファイルを入れる
    - 実行時に`tmp`ディレクトリにコピーされ、`tmp`ディレクトリ内のファイルに対してタグの書き換えを行う
1. main.pyを実行する
### 対応ファイル
- `.mp3`
- `.m4a`
    - iTunesで作成したAACフォーマットとALAC(Apple Lossless)で動作確認

## メモ
- mutagen
    - https://mutagen.readthedocs.io/en/latest/index.html
- ID3タグ
    - https://id3.org/id3v2.4.0-frames
    - https://id3.org/iTunes%20Compilation%20Flag
- タグの対照表
    - https://wiki.hydrogenaud.io/index.php?title=Tag_Mapping#Mapping_Tables
