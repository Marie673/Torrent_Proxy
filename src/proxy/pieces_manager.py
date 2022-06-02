import piece
import bitstring
from pubsub import pub
import time


class PiecesManager(object):
    def __init__(self, torrent):
        self.torrent = torrent
        self.number_of_pieces = int(torrent.number_of_pieces)
        self.pieces = self._generate_pieces()
        self.files = self._load_files()

        for file in self.files:
            id_piece = file['idPiece']
            self.pieces[id_piece].files.append(file)

        pub.subscribe(self.receive_block_piece, 'PiecesManager.Piece')

    def receive_block_piece(self, piece):
        piece_index, piece_offset, piece_data = piece
        self.pieces[piece_index].set_block(piece_offset, piece_data)

        if self.pieces[piece_index].are_all_blocks_full():
            if self.pieces[piece_index].set_to_full():
                tmp_path = '/'.join(["tmp", self.torrent.info_hash_str, str(piece_index)])
                self.pieces[piece_index].write_piece_on_disk(tmp_path)
                with open('~/exp/test.dat', mode='a') as file:
                    text = 'piece:' + self.torrent.info_hash_str + ":" + \
                           str(piece_index) + ":" + str(-1) + ":" + \
                           time.time()
                    file.write(text)

    def get_block(self, piece_index, block_offset, block_length):
        for piece in self.pieces:
            if piece_index == piece.piece_index:
                if piece.is_full:
                    return piece.get_block(block_offset, block_length)
                else:
                    break

        return None

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
