import bitstring
from src.domain.entity.piece.piece import Piece
from src.domain.entity.torrent import Torrent, Info, FileMode
from typing import List


class PiecesManager:
    def __init__(self, torrent: Torrent):
        self.info: Info = torrent.info
        if torrent.file_mode == FileMode.single_file:
            self.number_of_pieces = int(self.info.length / self.info.piece_length)
        else:
            length: int = 0
            for file in self.info.files:
                length += file.length
            self.number_of_pieces = int(length / self.info.piece_length)

        self.file_path = './' + torrent.path

        self.bitfield = bitstring.BitArray(self.number_of_pieces)
        self.pieces = self._generate_pieces()

        self.complete_pieces = 0

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
                self.complete_pieces += 1
                return

    def get_block(self, piece_index, block_offset, block_length) -> Piece:
        piece = self.pieces[piece_index]
        if piece_index == piece.piece_index:
            if piece.is_full:
                return piece.get_block(block_offset, block_length)
        # TODO 例外クラス作る
        raise Exception('Piece is not full')

    def all_pieces_completed(self) -> bool:
        for piece in self.pieces:
            if not piece.is_full:
                return False

        return True

    def _generate_pieces(self) -> List[Piece]:
        """
        torrentの全てのpieceを生成して初期化
        :return: List[Piece]
        """
        pieces: List[Piece] = []
        last_piece = self.number_of_pieces - 1

        for i in range(self.number_of_pieces):
            start = i * 20
            end = start + 20

            if i == last_piece:
                piece_length = self.info.length - (self.number_of_pieces - 1) * self.info.piece_length
                pieces.append(Piece(i, piece_length, self.info.pieces[start:end], self.file_path))
            else:
                pieces.append(Piece(i, self.info.piece_length, self.info.pieces[start:end], self.file_path))

        return pieces
