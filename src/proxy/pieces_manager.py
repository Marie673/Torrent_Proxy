import piece
import bitstring
from pubsub import pub


class PiecesManager(object):
    def __init__(self, torrent):
        self.torrent = torrent
        self.number_of_pieces = int(torrent.number_of_pieces)
        self.bitfield = bitstring.BitArray(self.number_of_pieces)
        self.pieces = self._generate_pieces()
        for piece in self.pieces:
            piece.tmp_path = 'tmp/' +str(self.torrent.info_hash.hex())

        self.complete_pieces = 0

        pub.subscribe(self.receive_block_piece, 'PiecesManager.Piece')
        pub.subscribe(self.update_bitfield, 'PiecesManager.PieceCompleted')

    def update_bitfield(self, piece_index):
        self.bitfield[piece_index] = 1

    def receive_block_piece(self, piece):
        piece_index, piece_offset, piece_data = piece

        if self.pieces[piece_index].is_full:
            return

        self.pieces[piece_index].set_block(piece_offset, piece_data)

        if self.pieces[piece_index].are_all_blocks_full():
            if self.pieces[piece_index].set_to_full():
                self.complete_pieces += 1

    def get_block(self, piece_index, block_offset, block_length):
        for piece in self.pieces:
            if piece_index == piece.piece_index:
                if piece.is_full:
                    return piece.get_block(block_offset, block_length)
                else:
                    break

        return None

    def all_pieces_completed(self):
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
                pieces.append(piece.Piece(i, piece_length, self.torrent.pieces[start:end]))
            else:
                pieces.append(piece.Piece(i, self.torrent.piece_length, self.torrent.pieces[start:end]))

        return pieces
