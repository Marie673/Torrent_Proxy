import asyncio
import math
import os.path
import time
from multiprocessing import Process, Queue

from src.application.bittorrent.bittorrent import BitTorrent
from src.domain.entity.torrent import Torrent
import cefpyco

import src.global_value as gv
from logger import logger


class Color:
    BLACK = '\033[30m'  # (文字)黒
    RED = '\033[31m'  # (文字)赤
    GREEN = '\033[32m'  # (文字)緑
    YELLOW = '\033[33m'  # (文字)黄
    BLUE = '\033[34m'  # (文字)青
    MAGENTA = '\033[35m'  # (文字)マゼンタ
    CYAN = '\033[36m'  # (文字)シアン
    WHITE = '\033[37m'  # (文字)白
    COLOR_DEFAULT = '\033[39m'  # 文字色をデフォルトに戻す
    BOLD = '\033[1m'  # 太字
    UNDERLINE = '\033[4m'  # 下線
    INVISIBLE = '\033[08m'  # 不可視
    REVERCE = '\033[07m'  # 文字色と背景色を反転
    BG_BLACK = '\033[40m'  # (背景)黒
    BG_RED = '\033[41m'  # (背景)赤
    BG_GREEN = '\033[42m'  # (背景)緑
    BG_YELLOW = '\033[43m'  # (背景)黄
    BG_BLUE = '\033[44m'  # (背景)青
    BG_MAGENTA = '\033[45m'  # (背景)マゼンタ
    BG_CYAN = '\033[46m'  # (背景)シアン
    BG_WHITE = '\033[47m'  # (背景)白
    BG_DEFAULT = '\033[49m'  # 背景色をデフォルトに戻す
    RESET = '\033[0m'  # 全てリセット


class InterestListener:
    def __init__(self):
        self.cef_handle = cefpyco.CefpycoHandle()
        self.cef_handle.begin()

        self.request_task = []
        self.bittorrent_task = []
        self.bittorrent_dict = {}

        self.queue = Queue()

    def run(self) -> None:
        self.cef_handle.register("ccnx:/BitTorrent")
        logger.debug("start interest_listener")
        translate_p = None
        try:
            translate_p = Process(target=self.translator)
            translate_p.start()
            while True:
                try:
                    info = self.cef_handle.receive()
                    # logger.debug(info)
                    if info.is_succeeded and info.is_interest:
                        self.handle_interest(info)
                except Exception as e:
                    logger.error(e)
        except KeyboardInterrupt:
            logger.debug("Interest Listener is down")
        finally:
            translate_p.kill()

        return

    def translator(self):
        async def routine():
            while True:
                while self.queue.qsize() > 0:
                    req = self.queue.get()
                    name, prefix, chunk_num, end_chunk_num = req
                    info_hash = prefix[2]

                    if info_hash not in self.bittorrent_dict:
                        # torrentファイルを持っている前提
                        # torrentファイルの名前は、{$info_hash} + ".torrent"
                        torrent_file_name = gv.TORRENT_FILE_PATH + info_hash + ".torrent"
                        torrent = Torrent(torrent_file_name)
                        b_thread = BitTorrent(torrent)
                        b_thread.start()
                        self.bittorrent_dict[info_hash] = b_thread

                    await self.handle_bittorrent(req)

        asyncio.run(routine())

    def handle_interest(self, info):
        name = info.name
        # logger.debug(name)
        prefix = name.split('/')
        """
        prefix[0] = ccnx:
        prefix[1] = BitTorrent
        prefix[2] = info_hash
        prefix[3] = piece_index
        """
        chunk_num = info.chunk_num
        end_chunk_num = info.end_chunk_num
        interest_info = (name, prefix, chunk_num, end_chunk_num)

        # logger.debug(prefix)
        if prefix[0] != "ccnx:":
            return

        if prefix[1] == "BitTorrent":
            # logger.debug("handle Bittorrent")
            self.queue.put(interest_info)

    async def handle_bittorrent(self, interest_info):
        (name, prefix, chunk_num, end_chunk_num) = interest_info
        info_hash = prefix[2]
        piece_index = int(prefix[3])
        logger.debug(f"{info_hash} {piece_index}")

        b_thread: BitTorrent = self.bittorrent_dict[info_hash]
        piece = b_thread.pieces[piece_index]

        # オフセットの計算
        offset = chunk_num * gv.CHUNK_SIZE

        # end_chunk_numの計算.
        # chunk_numは0から数え始めるので、-1する.
        end_chunk_num = math.ceil(piece.piece_size / gv.CHUNK_SIZE) - 1

        try:
            data: bytes = await asyncio.wait_for(
                b_thread.get_data(piece_index, offset, gv.CHUNK_SIZE),
                timeout=4
            )
        except asyncio.TimeoutError as e:
            logger.error(e)
            return
        except Exception as e:
            logger.error(e)
            return

        # logger.debug(f"send data:: index: {piece_index}, chunk: {chunk_num}")
        self.cef_handle.send_data(
            name=name,
            payload=data,
            chunk_num=chunk_num,
            end_chunk_num=end_chunk_num,
            cache_time=60  # たしかs
        )
