import os.path
import cefpyco


CEFORE_DIR = os.path.abspath("cefore")
peer_d: dict = {}


def searchPeer(info_hash: str) -> str:
    if info_hash in peer_d.keys():
        return peer_d[info_hash]


def addPeer(info_hash: str, uuid: str):
    with open("../cefore/cefnetd.conf", "a") as fib_table:
        print("ccnx:/BitTorrent/" + info_hash + " tcp " + uuid, file=fib_table)
    peer_d[info_hash] = uuid


def listener(handle: cefpyco.CefpycoHandle):
    handle.register("ccnx:/BitTorrent")
    print("start listening")
    while True:
        info = handle.receive()
        prefix = info.name.split('/')

        if info.is_interest:
            print("receive interest")
            if prefix[2] == 'I have piece':
                print("add new peer")
                info_hash = prefix[3]
                uuid = prefix[4]
                addPeer(info_hash, uuid)
                continue

            info_hash = prefix[2]
            peer = searchPeer(info_hash)
            print("send interest")
            handle.send_interest("ccnx:/BitTorrent/" + peer + "/" + info_hash, info.chunk_num)

        if info.is_data:
            print("receive data")
            info_hash = prefix[3]
            handle.send_data("ccnx:/BitTorrent/" + info_hash, info.payload, info.chunk_num)


def main():
    print("create handle...")
    with cefpyco.create_handle(enable_log=False, ceforedir=CEFORE_DIR) as handle:
        listener(handle)


if __name__ == '__main__':
    main()
