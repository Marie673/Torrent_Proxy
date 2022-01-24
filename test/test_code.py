import sys
import time

import cefpyco

SIZE=4096
NAME0='ccnx:/test/1M.dummy'
NAME1='ccnx:/test/10M.dummy'
NAME2='ccnx:/test/100M.dummy'

def get_data(info):
    return

def main():
    args = sys.argv
    if args[1] == '0':
        name = NAME0
    elif args[1] == '1':
        name = NAME1
    elif args[1] == '2':
        name = NAME2
    else:
        name = None
        exit(1)

    with cefpyco.create_handle() as h:
        h.send_interest(name, 0)
        start_time = time.time()
        while True:
            info = h.receive()
            if not info.is_succeeded:
                continue

            if info.is_data:
                print("get data " + str(info.chunk_num) + " " + str(info.end_chunk_num))
                get_data(info)
                if info.chunk_num != info.end_chunk_num:
                    h.send_interest(info.name, info.chunk_num+1)
                else:
                    get_data(info)
                    end_time = time.time() - start_time
                    print(end_time)

        print(end_time)

if __name__ == '__main__':
    main()