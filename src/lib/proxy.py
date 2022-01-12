import cefpyco
from threading import Thread


class Cef(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.handle = cefpyco.create_handle(enable_log=False)
        self.handle.begin()
        self.handle.register("ccnx:/BitTorrent")

    def run(self):
        while True:
            info = self.handle.receive()
            self._process_new_message(info)

    def _process_new_message(self, info):
        pass


def main():

    cef = Cef()
    cef.run()


if __name__ == '__main__':
    main()
