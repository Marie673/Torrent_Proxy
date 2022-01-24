import sys
import time

import cefpyco

NAME0='ccnx:/test/1M.dummy'
NAME1='ccnx:/test/10M.dummy'
NAME2='ccnx:/test/100M.dummy'

def get_data(info):
    return

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

    data_size = 0
    with cefpyco.create_handle() as h:
        h.send_interest(name, 0)
        start_time = time.time()
        while True:
            info = h.receive()
            if not info.is_succeeded:
                continue

            if info.is_data:
                data_size += len(info.payload)
                get_data(info)
                if info.chunk_num == 1:
                    for chunk_num in range(1, info.end_chunk_num):
                        for _ in range(3):
                            h.send_interest(name, chunk_num)
                if data_size == full_data_size:
                    end_time = time.time() - start_time
                    break

        print(end_time)
        print(data_size)

if __name__ == '__main__':
    main()