import sys
import threading
import time
from threading import Thread, Event

import cefpyco

NAME0='ccnx:/test/1M.dummy'
NAME1='ccnx:/test/10M.dummy'
NAME2='ccnx:/test/100M.dummy'


class Interest(object):
    def __init__(self, interest, chunk):
        self.interest = interest
        self.chunk = chunk
        self.time = None

    def send_interest(self, handle):
        self.time = time.time()
        handle.send_interest(self.interest, self.chunk)


class Cefore(object):
    def __init__(self, name):
        self.name = name
        self.handle = cefpyco.CefpycoHandle()
        self.handle.begin()
        self.bitfield = []
        self.data_size = 0
        self.active_state = True
        self.interests = {}
        self.t_listener = Thread(target=self.listener)

        self.t_listener.start()

    def display_progress(self):
        count = self.bitfield.count(True)
        print("[{}/{}]".format(count, len(self.bitfield)))

    def listener(self):
        print("listener starting")
        while self.active_state:
            info = self.handle.receive()

            if not info.is_succeeded:
                continue

            if info.is_data:
                if not self.bitfield:
                    self.bitfield = [False for _ in range(info.end_chunk_num)]
                    self.bitfield[info.chunk_num] = True
                    self.data_size += len(info.payload)
                    continue

                if info.chunk_num in self.interests:
                    del self.interests[info.chunk_num]

                if self.bitfield[info.chunk_num] is True:
                    continue

                self.bitfield[info.chunk_num] = True
                self.data_size += len(info.payload)

            # self.display_progress()

    def run(self):
        start_time = time.time()
        self.handle.send_interest(self.name, 0)
        while True:
            if len(self.bitfield) >= 1:
                break
        print("get first chunk")

        while False in self.bitfield:
            print(len(self.interests))
            for index in self.interests:
                i = self.interests[index]
                if time.time() - i.time > 2:
                    del self.interests[index]


            if len(self.interests) >= 3000:
                continue

            for chunk_num in range(len(self.bitfield)):
                if self.bitfield[chunk_num]:
                    continue

                interest = Interest(self.name, chunk_num)
                interest.send_interest(self.handle)
                self.interests[chunk_num] = interest

            time.sleep(0.1)

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
        cef.kill()


if __name__ == '__main__':
    main()