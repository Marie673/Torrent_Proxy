import bitstring

from lib.piece.piece import Piece

import yaml
from logging import getLogger
import logging.config

log_config = 'config.yaml'
logging.config.dictConfig(yaml.load(open(log_config).read(), Loader=yaml.SafeLoader))
logger = getLogger('develop')


class PiecesManager(object):
    def __init__(self, torrent):
        self.torrent = torrent
        self.number_of_pieces = int(torrent.number_of_pieces)
        self.bitfield = bitstring.BitArray(self.number_of_pieces)
        self.pieces = self._generate_pieces()
        self.files = self._load_files()
        self.complete_pieces = 0

        # トレントのファイル
        for file in self.files:
            id_piece = file['idPiece']
            self.pieces[id_piece].files.append(file)

    def update_piece_status(self):
        for piece in self.pieces:
            piece.update_block_status()

    def _update_bitfield(self, piece_index):
        piece = self.pieces[piece_index]
        if piece.is_full:
            self.bitfield[piece_index] = 1
        else:
            self.bitfield[piece_index] = 0

    def receive_block_piece(self, receive_piece_data):
        piece_index, piece_offset, piece_data = receive_piece_data

        if self.pieces[piece_index].is_full:
            return

        piece = self.pieces[piece_index]
        piece.set_block(piece_offset, piece_data)

        if piece.are_all_blocks_full():
            if piece.set_to_full():
                self._write_piece_on_disk(piece)
                self.complete_pieces += 1

    def _write_piece_on_disk(self, piece):
        for file in self.files:
            path_file = file["path"]
            file_offset = file["fileOffset"]
            piece_offset = file["pieceOffset"]
            length = file["length"]

            # TODO mutex処理追加
            try:
                f = open(path_file, 'r+b')  # Already existing file
            except IOError:
                f = open(path_file, 'wb')  # New file

            f.seek(file_offset)
            # 結合度高い
            f.write(piece.raw_data[piece_offset:piece_offset + length])
            f.close()

        # TODO piece reset関数をPieceに追加
        piece.exist = True
        piece.raw_data = b''
        piece.blocks = []

    def get_block(self, piece_index, block_offset, block_length) -> Piece:
        piece = self.pieces[piece_index]
        if piece_index == piece.piece_index:
            if piece.is_full:
                return piece.get_block(block_offset, block_length)
        # TODO 例外クラス作る
        raise Exception('Piece is not full')

    def get_piece(self, piece_index):
        piece = self.pieces[piece_index]
        if piece.exist:
            with open(self.files[0]["path"], "r+b") as file:
                data = file.read()
                return data

        return None

    def all_pieces_completed(self) -> bool:
        for piece in self.pieces:
            if not piece.is_full:
                return False

        return True

    def _generate_pieces(self):
        pieces = []
        last_piece = self.number_of_pieces - 1

        for i in range(self.number_of_pieces):
            start = i * 20
            end = start + 20

            if i == last_piece:
                piece_length = self.torrent.total_length - (self.number_of_pieces - 1) * self.torrent.piece_length
                pieces.append(Piece(i, piece_length, self.torrent.pieces[start:end]))
            else:
                pieces.append(Piece(i, self.torrent.piece_length, self.torrent.pieces[start:end]))

        return pieces

    def _load_files(self):
        files = []
        piece_offset = 0
        piece_size_used = 0

        for f in self.torrent.file_names:
            current_size_file = f["length"]
            file_offset = 0

            while current_size_file > 0:
                id_piece = int(piece_offset / self.torrent.piece_length)
                piece_size = self.pieces[id_piece].piece_size - piece_size_used

                if current_size_file - piece_size < 0:
                    file = {"length": current_size_file,
                            "idPiece": id_piece,
                            "fileOffset": file_offset,
                            "pieceOffset": piece_size_used,
                            "path": f["path"]
                            }
                    piece_offset += current_size_file
                    file_offset += current_size_file
                    piece_size_used += current_size_file
                    current_size_file = 0

                else:
                    current_size_file -= piece_size
                    file = {"length": piece_size,
                            "idPiece": id_piece,
                            "fileOffset": file_offset,
                            "pieceOffset": piece_size_used,
                            "path": f["path"]
                            }
                    piece_offset += piece_size
                    file_offset += piece_size
                    piece_size_used = 0

                files.append(file)
        return files
