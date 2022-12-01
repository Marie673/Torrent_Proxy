from application.bittorrent.bittorrent import BitTorrent, CommunicationManager
from application.interest_listener import InterestListener


def main():
    com_mgr = CommunicationManager()
    interest_listener = InterestListener()

    com_mgr.start()
    interest_listener.start()

    queue = []
    while True:
        for request in queue:
            info_hash, piece_index = request
            # ピースファイルが存在すればDataを送信
            # 無ければBitTorrentで要求


if __name__ == '__main__':
    main()
