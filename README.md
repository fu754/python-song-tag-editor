# 自分用：楽曲ファイルのタグ情報の一括編集スクリプト
- 同じディレクトリ内で複数アーティストが存在したときにコンピレーションアルバムのフラグを有効にする
    - 上記の条件を満たす場合にアルバムアーティストが設定されていなかった場合に`VARIOUS_ALBUM_ARTIST: Final[str] = 'Various Artist'`へ文字列置換を行う

## メモ
- https://mutagen.readthedocs.io/en/latest/index.html
- https://id3.org/id3v2.4.0-frames
- https://id3.org/iTunes%20Compilation%20Flag
- https://wiki.hydrogenaud.io/index.php?title=Tag_Mapping#Mapping_Tables