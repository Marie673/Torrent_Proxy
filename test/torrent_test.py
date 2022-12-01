from src.domain.entity.torrent import Torrent


if __name__ == '__main__':
    path = 'ubuntu-22.10-desktop-amd64.iso.torrent'
    torrent = Torrent(path)
    print(torrent.__str__())
