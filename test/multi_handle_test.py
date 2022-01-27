import time

import cefpyco
from multiprocessing import Process

MAX = 3

def create_cefhandle():
    handle = cefpyco.CefpycoHandle()
    handle.begin()
    time.sleep(100)


def main():
    for i in range(MAX):
        p = Process(target=create_cefhandle)
        p.start()

if __name__ == "__main__":
    main()