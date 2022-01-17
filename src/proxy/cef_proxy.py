from threading import Thread
import cefpyco
import downloader
from pubsub import pub


class Cef(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.name = 'ccnx:/BitTorrent/'
        self.handle = cefpyco.CefpycoHandle()
        self.message = []
        self.torrent: dict = {}
        self.is_active = True

        pub.subscribe(self.send_data, 'Cef.SendPiece')

    def run(self):
        self.handle.begin()
        self.handle.register(self.name)

        while self.is_active:
            info = self.handle.receive()
            if info.is_succeeded:
                self.message.append(info)

            for message in self.message:
                self._process_new_message(message)

    def _process_new_message(self, info: cefpyco.core.CcnPacketInfo):
        prefix = info.name.split("/")
        """
        prefix[0] == 'ccnx:'
        prefix[1] == 'BitTorrent'
        prefix[2] == 'info_hash'
        prefix[3] == id {
            id == 6: request message
            id == torrent: torrent file(This is ID considering that the proxy 
                                        does not have torrent files) 
            }
        """
        if info.is_interest:
            if prefix[0] != 'ccnx:' or prefix[1] != 'BitTorrent':
                return

            if prefix[2] not in self.torrent:
                interest = self.name + prefix[2] + "/torrent"
                self.handle.send_interest(interest)

            if prefix[3] == '6' or prefix[3] == 'request':
                downloader.Run(self.torrent[prefix[2]]).start()

        if info.is_data:
            if prefix[3] == 'torrent':
                self.torrent[prefix[2]] = info.payload

    def send_data(self, name, payload):
        self.handle.send_data(name, payload)


def main():
    pass


if __name__ == '__main__':
    main()
