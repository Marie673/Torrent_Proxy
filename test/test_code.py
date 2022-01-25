import sys
import threading
import time
from threading import Thread

import cefpyco

NAME0='ccnx:/test/1M.dummy'
NAME1='ccnx:/test/10M.dummy'
NAME2='ccnx:/test/100M.dummy'


MAX_INTEREST = 1000
BLOCK_SIZE = 30

alive = True


class Cefore(object):
    def __init__(self, name):
        self.name = name
        self.handle = cefpyco.CefpycoHandle()
        self.handle.begin()
        self.bitfield = []
        self.data_size = 0
        self.active_state = True
        self.interests = {}

    def display_progress(self):
        count = self.bitfield.count(True)
        print("[{}/{}]".format(count, len(self.bitfield)))

    def handle_interest(self, info):
        if not self.bitfield:
            self.bitfield = [False for _ in range(info.end_chunk_num)]
            self.bitfield[info.chunk_num] = True
            self.data_size += len(info.payload)
            return

        if info.chunk_num in self.interests:
            del self.interests[info.chunk_num]

        if self.bitfield[info.chunk_num] is True:
            return

        self.bitfield[info.chunk_num] = True
        self.data_size += len(info.payload)

    def run(self):
        start_time = time.time()
        self.handle.send_interest(self.name, 0)
        while True:
            if len(self.bitfield) >= 1:
                break
        print("get first chunk")

        padding = self.bitfield
        for chunk in range(1, MAX_INTEREST):
            self.handle.send_interest(self.name, chunk)
            padding[chunk] = True

        while False in self.bitfield:
            info = self.handle.receive()
            if not info.is_succeeded:
                continue
            else:
                self.handle_interest(info)

            chunk = padding.index(False)
            self.handle.send_interest(self.name, chunk)
            padding[chunk] = True

        self.active_state = False
        end_time = time.time() - start_time
        throughput = (self.data_size / (1024*1024)) / end_time
        print("time:{}[sec] data size: {}[byte]".format(end_time,
                                                        self.data_size))
        print("throughput: {}".format(round(throughput, 2)))


def main():
    args = sys.argv
    name: str = ""
    full_data_size: int = 0
    if args[1] == '0':
        name = NAME0
        full_data_size = 1024 * 1024
    elif args[1] == '1':
        name = NAME1
        full_data_size = 1024 * 1024 * 10
    elif args[1] == '2':
        name = NAME2
        full_data_size = 1024 * 1024 * 100
    else:
        exit(1)

    cef = Cefore(name)
    try:
        cef.run()
    except KeyboardInterrupt:
        alive = False



if __name__ == '__main__':
    main()