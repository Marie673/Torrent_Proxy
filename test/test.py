import cefpyco

SIZE=4096

def send_data(h, name, payload):
    cache_time = 360000  # 1時間
    chunk_num = 0
    end_chunk_num = len(payload) // SIZE
    while payload:
        chunk = payload[:SIZE]
        h.send_data(name=name, payload=chunk,
                                  chunk_num=chunk_num, end_chunk_num=end_chunk_num, cache_time=cache_time)
        payload = payload[SIZE:]
        chunk_num += 1

def main():
    with cefpyco.create_handle() as h:
        h.register("ccnx:/test")
        while True:
            info = h.receive()
            if not info.is_succeeded:
                continue

            name = info.name.split("/")
            if info.is_interest:
                print('get interest')
                if name[2] == '1M.dummy' or name[2] == '10M.dummy' or name[2] == '100M.dummy':
                    with open(name[2], "rb") as file:
                        payload = file.read()
                        file.close()
                        send_data(h, info.name, payload)


if __name__ == '__main__':
    main()