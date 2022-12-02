import math
from typing import List
import hashlib
import time
import signal

from src.domain.entity.piece.block import Block, BLOCK_SIZE, State

import yaml
import logging.config
from logging import getLogger
log_config = 'config.yaml'
logging.config.dictConfig(yaml.load(open(log_config).read(), Loader=yaml.SafeLoader))
logger = getLogger('develop')

PENDING_TIME = 5


class Piece(object):
    def __init__(self, piece_index: int, piece_size: int, piece_hash: str, file_path):
        self.exist = False

        self.piece_index = piece_index
        self.piece_size = piece_size
        self.piece_hash = piece_hash

        self.is_full: bool = False
        # pieceが保管されているディレクトリのパス
        self.file_path = file_path + '/' + str(piece_index)
        self.number_of_blocks: int = int(math.ceil(float(piece_size) / BLOCK_SIZE))

        self.raw_data: bytes = b''
        self.blocks: List[Block] = []

        self._init_blocks()
        signal.signal(signal.SIGALRM, self.update_block_status)
        signal.setitimer(signal.ITIMER_REAL, 1, 5)

    def update_block_status(self, signum, frame):  # if block is pending for too long : set it free
        for i, block in enumerate(self.blocks):
            if block.state == State.PENDING and (time.time() - block.last_seen) > PENDING_TIME:
                self.blocks[i] = Block()

    def set_block(self, offset, data):
        index = int(offset / BLOCK_SIZE)

        if not self.is_full and not self.blocks[index].state == State.FULL:
            self.blocks[index].data = data
            self.blocks[index].state = State.FULL

    def get_block(self, block_offset, block_length):
        if self.exist:
            for path_file in self.file_path:
                with open(path_file, 'r+b') as file:
                    data = file.read()
                    return data[block_offset:block_length]
        else:
            # TODO: 例外処理の追加　file is not full block
            pass

        return self.raw_data[block_offset:block_length]

    def get_empty_block(self):
        if self.is_full:
            return None

        for block_index, block in enumerate(self.blocks):
            if block.state == State.FREE:
                self.blocks[block_index].state = State.PENDING
                self.blocks[block_index].last_seen = time.time()
                return self.piece_index, block_index * BLOCK_SIZE, block.block_size

        return None

    def are_all_blocks_full(self):
        for block in self.blocks:
            if block.state == State.FREE or block.state == State.PENDING:
                return False

        return True

    def set_to_full(self):
        data = self._merge_blocks()
        if not self._valid_blocks(data):
            self._init_blocks()
            return False

        self.is_full = True
        self.raw_data = data

        return True

    def _init_blocks(self):
        self.blocks = []

        if self.number_of_blocks > 1:
            for i in range(self.number_of_blocks):
                self.blocks.append(Block())

            if (self.piece_size % BLOCK_SIZE) > 0:
                self.blocks[self.number_of_blocks - 1].block_size = self.piece_size % BLOCK_SIZE

        else:
            self.blocks.append(Block(block_size=int(self.piece_size)))

    def _merge_blocks(self):
        buf = b''

        for block in self.blocks:
            buf += block.data

        return buf

    def _valid_blocks(self, piece_raw_data):
        hashed_piece_raw_data = hashlib.sha1(piece_raw_data).digest()

        if hashed_piece_raw_data == self.piece_hash:
            return True

        logger.warning("Error Piece Hash")
        logger.debug("{} : {}".format(hashed_piece_raw_data, self.piece_hash))
        return False

    def write_on_disk(self):
        with open(self.file_path, "wb") as file:
            file.write(self.raw_data)
