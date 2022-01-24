import os

import cefpyco

SIZE = 1024 * 7

def send_file(h, info, file_name):
    cache_time = 360000  # 1時間
    file_size = os.path.getsize(file_name)
    end_chunk_num = file_size // SIZE
    chunk = info.chunk_num
    seek = chunk * SIZE
    name = info.name
    with open(file_name, "rb") as file:
        file.seek(seek)
        payload = file.read(SIZE)
        h.send_data(name=name, payload=payload,
                    chunk_num=chunk, end_chunk_num=end_chunk_num, cache_time=cache_time)

def main():
    with cefpyco.create_handle() as h:
        h.register("ccnx:/test")
        while True:
            info = h.receive()
            if not info.is_succeeded:
                continue

            name = info.name.split("/")
            if info.is_interest:
                # print('get interest')
                if name[2] == '1M.dummy' or name[2] == '10M.dummy' or name[2] == '100M.dummy':
                    send_file(h, info, name[2])


if __name__ == '__main__':
    main()