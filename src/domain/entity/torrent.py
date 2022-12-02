import enum
import hashlib
from typing import List
from bcoding import bdecode, bencode
import logging

"""
ファイル構造
announce - トラッカーのURL
info - 各ファイルが対応するDict
    # 下記キーであるfiles, lengthはシングルファイルまたはマルチファイルに対応してどちらかのみが存在
    files - 各ファイルが対応するDict　複数のファイルが共有されている場合のみ使用
        length - ファイルのサイズ　バイト単位
        path - サブディレクトリ名に対応する文字列のリスト　最後の文字列が実際のファイル名
    length - ファイルの大きさ　バイト単位　１つのファイルを共有する場合のみ使用

    name - 保存先のファイル名候補(シングルファイル)/保存先のディレクトリ名候補(マルチファイル)
    piece length - 1ピースのバイト数　一般的に 2^8KB = 256KB = 262,144B
    pieces - ハッシュリスト 各pieceのSHA-1ハッシュを連結したもの
            SHA1は160ビットのハッシュを返すため、pieceは20バイトの倍数の文字列
"""


class FileMode(enum.Enum):
    single_file = enum.auto()
    multiple_file = enum.auto()


class Files:
    length: int
    path: str


class Info:
    files: List[Files]
    length: int
    name: str
    piece_length: int
    pieces: str


class Torrent(object):
    torrent: dict

    announce: str
    announce_list: list
    nodes: list

    info: Info
    info_hash: bytes
    info_hash_hex: str
    file_mode: FileMode

    def __init__(self, path: str):
        self.path: str = path  # torrentファイルが保存されているパス
        torrent: dict = self.load_from_path(self.path)

        if 'announce' in torrent.keys():
            self.announce = torrent['announce']
        if 'announce-list' in torrent.keys():
            self.announce_list = torrent['announce-list']
        if 'nodes' in torrent.keys():
            self.nodes = torrent['nodes']

        if 'info' in torrent.keys():
            new_info: Info = Info()
            self.info_hash = hashlib.sha1(bencode(torrent['info'])).digest()
            self.info_hash_hex = str(self.info_hash.hex())
            if 'files' in torrent['info'].keys():
                self.file_mode = FileMode.multiple_file
                new_info.files = []
                files: List[dict] = torrent['info']['files']
                for file_dict in files:
                    new_file: Files = Files()
                    new_file.length = file_dict['length']
                    new_file.path = file_dict['path']
                    new_info.files.append(new_file)
            elif 'length' in torrent['info'].keys():
                self.file_mode = FileMode.single_file
                new_info.length = torrent['info']['length']
            if 'name' in torrent['info'].keys():
                new_info.name = torrent['info']['name']
            if 'piece length' in torrent['info'].keys():
                new_info.piece_length = torrent['info']['piece length']
            if 'pieces' in torrent['info'].keys():
                new_info.pieces = torrent['info']['pieces']
            self.info = new_info

    @staticmethod
    def load_from_path(path):
        logging.debug('start load_from_path')
        with open(path, 'rb') as file:
            torrent = bdecode(file)
            return torrent

    def __str__(self):
        try:
            print(f'announce: {self.announce}')
        except AttributeError:
            pass
        try:
            print(f'announce-list: {self.announce_list}')
        except AttributeError:
            pass
        try:
            print(f'nodes: {self.nodes}')
        except AttributeError:
            pass

        try:
            print('info:')
            if hasattr(self.info, 'files'):
                print('  files:')
                for file in self.info.files:
                    print(f'    length: {file.length}')
                    print(f'    path: {file.path}')
            else:
                print(f'  length: {self.info.length}')
            print(f'  name: {self.info.name}')
            print(f'  piece_length: {self.info.piece_length}')
            print(f'  pieces: {self.info.pieces[:10]} ... '
                  f'size is {len(self.info.pieces)}')
        except AttributeError:
            pass

        try:
            print(f'info_hash: {self.info_hash_hex}')
        except AttributeError:
            pass

        return
