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
    bitfield = [False]
    with cefpyco.create_handle() as h:
        h.send_interest(name, 0)
        start_time = time.time()
        while True:
            info = h.receive()
            if not info.is_succeeded:
                continue

            if info.is_data:
                if bitfield[info.chunk_num] is True:
                    continue

                if info.chunk_num == 0:
                    bitfield = [False for _ in range(info.end_chunk_num)]
                    bitfield[0] = True
                    data_size += len(info.payload)
                    print("send interest")
                    for chunk_num in range(1, info.end_chunk_num):
                        for _ in range(3):
                            h.send_interest(name, chunk_num)

                bitfield[info.chunk_num] = True
                print("get data {}".format(info.chunk_num))
                data_size += len(info.payload)

                if False in bitfield:
                    continue
                else:
                    end_time = time.time() - start_time
                    break

        print(end_time)
        print(data_size)

if __name__ == '__main__':
    main()