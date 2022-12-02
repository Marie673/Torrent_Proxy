from src.domain.entity.piece.piece import Piece


@staticmethod
class PieceRepository:
    @staticmethod
    def save(piece: Piece):
        with open(piece.file_path, "wb") as file:
            file.write(piece.raw_data)
        return

    @staticmethod
    def delete(piece_index: int):
        return

    @staticmethod
    def get_piece(piece: Piece):
        with open(piece.file_path, "rb") as file:
            data = file.read()
            piece.raw_data = data

            return data
