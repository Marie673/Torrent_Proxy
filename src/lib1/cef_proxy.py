from threading import Thread
import cefpyco


class Cef(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.name = 'ccnx:/BitTorrent'
        self.handle = cefpyco.CefpycoHandle()
        self.message = []
        self.is_active = True

    def run(self):
        self.handle.begin()
        self.handle.register(self.name)

        while self.is_active:
            info = self.handle.receive()
            if info.is_succeeded:
                self.message.append(info)

            for message in self.message:
                self._process_new_message(message)

    def _process_new_message(self, info):
        if info.is_interest:





def main():
    pass


if __name__ == '__main__':
    main()
