import pytest

from src.domain.entity.torrent import Torrent
from src.application.bittorrent.bittorrent import BitTorrent, CommunicationManager
from src.domain.entity.tracker import Tracker


def torrent_test():
    path = 'ubuntu-22.10-desktop-amd64.iso.torrent'
    torrent = Torrent(path)
    print(torrent.__str__())


def tracker_test():
    path = 'ubuntu-22.10-desktop-amd64.iso.torrent'
    torrent = Torrent(path)
    tracker = Tracker(torrent)
    peers = tracker.get_peers_from_trackers()
    for peer in peers:
        print(peer)


def bittorrent_test():
    path = 'ubuntu-22.10-desktop-amd64.iso.torrent'
    torrent = Torrent(path)
    com_mgr = CommunicationManager()
    com_mgr.start()
    bittorrent = BitTorrent(torrent, com_mgr)
    bittorrent.start()


bittorrent_test()
