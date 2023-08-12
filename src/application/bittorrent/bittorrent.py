import asyncio
import datetime
import os
import random
import time
import bitstring

from threading import Thread

from src.domain.entity.piece.piece import Piece, State
from src.domain.entity.peer import Peer
from src.domain.entity.message import Request
from src.domain.entity.tracker import Tracker
from src.domain.entity.torrent import Torrent, Info, FileMode
from src.application.bittorrent.communication_manager import CommunicationManager
from typing import List
import src.global_value as gv

from logger import logger


class AlreadyRequested(Exception):
    pass


class BitTorrent(Thread):
    def __init__(self, torrent: Torrent):
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
        self.com_mgr = CommunicationManager(self)
        self.com_mgr.start()

        self.torrent = torrent
        self.info: Info = torrent.info
        self.info_hash = torrent.info_hash
        self.info_hash_hex = torrent.info_hash_hex
        self.file_path = gv.CACHE_PATH + self.torrent.info_hash_hex
        try:
            os.makedirs(self.file_path)
        except Exception as e:
            logger.error(e)

        # 1ピースのサイズ
        self.piece_length = self.info.piece_length
        # ピース数 の計算
        # シングルファイルと複数ファイルで計算方法が変わる. 複数ファイルの場合、ファイルのサイズの合計値が全体のデータサイズになる.
        if torrent.file_mode == FileMode.single_file:
            self.number_of_pieces = int(self.info.length / self.piece_length)
        else:
            length: int = 0
            for file in self.info.files:
                length += file.length
            self.number_of_pieces = int(length / self.piece_length)

        self.bitfield = bitstring.BitArray(self.number_of_pieces)
        self.pieces = self._generate_pieces()
        self.complete_pieces = 0

        """
        if gv.EVALUATION:
            with open(gv.EVALUATION_PATH, "a") as file:
                data = str(datetime.datetime.now()) + " bittorrent process is start\n"
                file.write(data)
        """
        self.lock = asyncio.Lock()
        self.timer = time.time()
        logger.debug(f"start {self.info_hash_hex} thread")

    def run(self) -> None:
        try:
            while True:
                if not self.com_mgr.has_unchocked_peers(self.info_hash) or \
                        len(self.com_mgr.peers) < gv.MAX_PEER_CONNECT:
                    self.add_peers_from_tracker()
                time.sleep(10)
                # await asyncio.sleep(10)

        except KeyboardInterrupt:
            logger.debug("bittorrent process: catch KeyboadInterrupt")
        finally:
            logger.debug("bittorrent process is down")

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
                    if _peer.ip == peer_candidate.ip:
                        return True
                return False
            if equivalence_detection():
                continue

            peer = Peer(self.info_hash, self.number_of_pieces, peer_candidate.ip, peer_candidate.port)
            if peer.do_handshake():
                logger.debug("add new peer" + peer.ip)
                self.com_mgr.peers.append(peer)

            if len(self.com_mgr.peers) >= gv.MAX_PEER_CONNECT:
                return

    def request_piece(self, piece_index):
        """
        just send message. this function don't wait for response.
        make blocks request to many peers.
        """
        piece = self.pieces[piece_index]
        if piece.catch_timeout():
            piece.state = State.FREE

        if piece.state == State.PENDING:
            raise AlreadyRequested('this piece is already requested.')

        logger.debug(f"BitTorrent {piece_index} request")
        piece.state = State.PENDING

        for block_index in range(piece.number_of_blocks):
            peer = self._get_random_peer_having_piece(piece_index)
            if not peer:
                logger.debug("not exist having peer")
                return
            block_data = self.pieces[piece_index].get_empty_block()
            if not block_data:
                # logger.debug("not block data")
                continue
            piece_index, block_offset, block_length = block_data
            message = Request(piece_index, block_offset, block_length).to_bytes()
            peer.send_to_peer(message)
            logger.debug(f"BitTorrent {piece_index} {block_offset} request")

    def _get_random_peer_having_piece(self, piece_index) -> Peer:
        ready_peer = []
        for peer in self.com_mgr.peers:
            if peer.info_hash is not self.info_hash:
                continue

            # logger.debug(f"{peer.is_eligible()}, {peer.is_unchoked()}, {peer.am_interested()}, {peer.has_piece(piece_index)}")
            if peer.is_eligible() and peer.is_unchoked() and peer.am_interested() and peer.has_piece(piece_index):
                ready_peer.append(peer)
        return random.choice(ready_peer) if ready_peer else None

    def receive_block_piece(self, receive_piece_data):
        piece_index, piece_offset, piece_data = receive_piece_data

        if self.pieces[piece_index].is_full:
            return

        piece = self.pieces[piece_index]
        piece.set_block(piece_offset, piece_data)
        logger.debug(f"bittorrent get piece {piece_index} {piece_offset}")

        if piece.are_all_blocks_full():
            if piece.set_to_full():
                logger.debug(f"bittorrent {piece_index} is full")
                self.complete_pieces += 1
                self.bitfield[piece_index] = 1
                piece.write_on_disk()
                logger.debug(f"{piece_index}, piece")
                return

    async def get_data(self, piece_index, block_offset, block_length) -> bytes:
        piece = self.pieces[piece_index]
        if piece.is_full:
            return piece.get_block(block_offset, block_length)

        try:
            self.request_piece(piece_index)
        except AlreadyRequested:
            raise AlreadyRequested('the piece is already requested.')

        while not piece.is_full:
            await asyncio.sleep(0)

        return piece.get_block(block_offset, block_length)

    def all_pieces_completed(self) -> bool:
        for piece in self.pieces:
            if not piece.is_full:
                return False

        return True

