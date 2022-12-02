import datetime
import os
import random
from threading import Thread
import bitstring
from src.domain.entity.piece.piece import Piece
from src.domain.entity.peer import Peer
from src.domain.entity.message import Request
from src.domain.entity.tracker import Tracker
from src.domain.entity.torrent import Torrent, Info, FileMode
from src.application.bittorrent.communication_manager import CommunicationManager
from typing import List


CACHE_PATH = os.environ['HOME']+"/proxy_cache/"
MAX_PEER_CONNECT = 200
EVALUATION = True
EVALUATION_PATH = os.environ['HOME']+"/evaluation/bittorrent/"


class BitTorrent(Thread):
    def __init__(self, torrent: Torrent, communication_manager: CommunicationManager):
        """
        トラッカーにアクセス
        ↓
        コンテンツを持っているピアのアドレスを取得
        ↓
        ピアとハンドシェイク (Peerでハンドシェイクを行う)
        ↓
        コンテンツの交換
        """
        super().__init__()
        self.com_mgr = communication_manager
        self.torrent = torrent
        self.info: Info = torrent.info
        self.info_hash = torrent.info_hash_hex
        self.file_path = CACHE_PATH + self.info.name
        os.makedirs(self.file_path)
        # number_of_pieces の計算
        if torrent.file_mode == FileMode.single_file:
            self.number_of_pieces = int(self.info.length / self.info.piece_length)
        else:
            length: int = 0
            for file in self.info.files:
                length += file.length
            self.number_of_pieces = int(length / self.info.piece_length)

        self.bitfield = bitstring.BitArray(self.number_of_pieces)
        self.pieces = self._generate_pieces()
        self.complete_pieces = 0

        if EVALUATION:
            with open(EVALUATION_PATH, "a") as file:
                data = str(datetime.datetime.now()) + " bittorrent process is start"
                file.write(data)

    def run(self) -> None:
        while not self.all_pieces_completed():
            if not self.com_mgr.has_unchocked_peers(self.info_hash):
                self.add_peers_from_tracker()
                continue

            for index, piece in enumerate(self.pieces):
                if piece.is_full:
                    continue
                self.request_piece(index)

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

    def add_peers_from_tracker(self):
        tracker = Tracker(self.torrent)
        new_peer_candidates: dict = tracker.get_peers_from_trackers()
        for peer_candidate in new_peer_candidates.values():
            def equivalence_detection():
                for _peer in self.com_mgr.peers:
                    if _peer.__hash__() is peer_candidate.__hash__():
                        return True
                return False
            if equivalence_detection():
                continue

            peer = Peer(self.info_hash, self.number_of_pieces, peer_candidate.ip, peer_candidate.port)
            if peer.do_handshake():
                self.com_mgr.peers.append(peer)

            if len(self.com_mgr.peers) >= MAX_PEER_CONNECT:
                return

    def request_piece(self, piece_index):
        """
        just send message. this function don't wait for response.
        make blocks request to many peers.
        """
        piece = self.pieces[piece_index]

        for block_index in range(piece.number_of_blocks):
            peer = self._get_random_peer_having_piece(piece_index)
            if not peer:
                return
            block_data = self.pieces[piece_index].get_empty_block()
            if not block_data:
                continue
            piece_index, block_offset, block_length = block_data
            message = Request(piece_index, block_offset, block_length).to_bytes()
            peer.send_to_peer(message)

        if EVALUATION:
            with open(EVALUATION_PATH, "a") as file:
                data = str(datetime.datetime.now()) + f" piece_index: {piece_index}, status: send_request"
                file.write(data)

    def _get_random_peer_having_piece(self, piece_index) -> Peer:
        ready_peer = []
        for peer in self.com_mgr.peers:
            if peer.info_hash is not self.info_hash:
                continue

            if peer.is_eligible() and peer.is_unchoked() and peer.am_interested() and peer.has_piece(piece_index):
                ready_peer.append(peer)

        return random.choice(ready_peer) if ready_peer else None

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
                piece.write_on_disk()
                if EVALUATION:
                    with open(EVALUATION_PATH, "a") as file:
                        data = str(datetime.datetime.now()) + f" piece_index: {piece_index}, status: complete"
                        file.write(data)
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
