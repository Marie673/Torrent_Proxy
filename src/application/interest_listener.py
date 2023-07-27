import asyncio
import os.path
import time
from src.application.bittorrent.bittorrent import BitTorrent
from src.domain.entity.torrent import Torrent
import cefpyco
import src.global_value as gv


from logger import logger


class InterestListener:
    def __init__(self):
        self.cef_handle = cefpyco.CefpycoHandle()
        self.cef_handle.begin()

        self.request_task = []
        self.bittorrent_task = []
        self.bittorrent_dict = {}

    async def run(self) -> None:
        self.cef_handle.register("ccnx:/BitTorrent")
        logger.debug("start interest_listener")
        try:
            while True:
                try:
                    info = self.cef_handle.receive()
                    # logger.debug(info)
                    if info.is_succeeded and info.is_interest :
                        await self.handle_interest(info)
                except Exception as e:
                    logger.error(e)
        except KeyboardInterrupt:
            logger.debug("Interest Listener is down")
            return

    async def handle_interest(self, info):
        name = info.name
        logger.debug(name)
        prefix = name.split('/')
        """
        prefix[0] = ccnx:
        prefix[1] = BitTorrent
        prefix[2] = info_hash
        """
        chunk_num = info.chunk_num
        end_chunk_num = info.end_chunk_num
        interest_info = (name, prefix, chunk_num, end_chunk_num)

        logger.debug(prefix)
        if prefix[0] != "ccnx:":
            return

        if prefix[1] == "BitTorrent":
            # logger.debug("handle Bittorrent")
            await self.handle_bittorrent(interest_info)

    async def handle_bittorrent(self, interest_info):
        (name, prefix, chunk_num, end_chunk_num) = interest_info
        info_hash = prefix[2]
        logger.debug(info_hash)

        if not info_hash in self.bittorrent_dict:
            # torrentファイルを持っている前提
            # torrentファイルの名前は、{$info_hash} + ".torrent"
            torrent_file_name = gv.TORRENT_FILE_PATH + info_hash + ".torrent"
            torrent = Torrent(torrent_file_name)
            b_process = BitTorrent(torrent)
            b_process.start()
            self.bittorrent_dict[info_hash] = b_process

        b_process: BitTorrent = self.bittorrent_dict[info_hash]

        # 1ピース当たりのチャンク数
        # ピースの最後を表現するときに、チャンクサイズで余りが出ても次のピースデータを含めない.
        if b_process.piece_length % gv.CHUNK_SIZE == 0:
            chunks_per_piece = b_process.piece_length // gv.CHUNK_SIZE
        else:
            chunks_per_piece = (b_process.piece_length // gv.CHUNK_SIZE) + 1

        # オフセットの計算
        piece_index = chunk_num // chunks_per_piece
        offset = (chunk_num % chunks_per_piece) * gv.CHUNK_SIZE

        # end_chunk_numの計算.
        # chunk_numは0から数え始めるので、-1する.
        end_chunk_num = chunks_per_piece * b_process.number_of_pieces - 1

        try:
            data: bytes = await asyncio.wait_for(
                b_process.get_data(piece_index, offset, gv.CHUNK_SIZE)
                , timeout=4
            )
        except asyncio.TimeoutError as e:
            raise e

        logger.debug(f"send data: {name}, chunk: {chunk_num}")
        self.cef_handle.send_data(
            name=name,
            payload=data,
            chunk_num=chunk_num,
            end_chunk_num=end_chunk_num,
            cache_time=60  # たしかs
        )
