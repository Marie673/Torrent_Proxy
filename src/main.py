import src.application.bittorrent.bittorrent as b
import src.application.bittorrent.communication_manager as c
from src.application.interest_listener import InterestListener
from src.domain.entity.torrent import Torrent
from typing import List


def main():
    com_mgr = c.CommunicationManager()
    interest_listener = InterestListener()

    com_mgr.start()
    interest_listener.start()

    path = 'ubuntu-22.10-desktop-amd64.iso.torrent'
    torrent = Torrent(path)

    t = b.BitTorrent(torrent, com_mgr)
    t.start()
    threads.append(t)

    """queue = []
    while True:
        for request in queue:
            info_hash, piece_index = request
            # ピースファイルが存在すればDataを送信
            # 無ければBitTorrentで要求"""


if __name__ == '__main__':
    threads: List[b.BitTorrent] = []
    main()
