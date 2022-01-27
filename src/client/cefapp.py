import logging
import numpy as np
from pubsub import pub
import cefpyco

from piece import Piece

class CefAppRunningInfo(object):
    def __init__(self, name, end_chunk_num):
        self.name = name
        self.end_chunk_num = end_chunk_num
        self.num_of_finished = 0
        self.finished_flag = np.zeros(end_chunk_num + 1)
        self.finished_flag[0] = 1
        self.timeout_count = 0


class CefAppConsumer:
    def __init__(self, name, piece, port,
                 pipeline=1000, timeout_limit=10):

        self.cef_handle = cefpyco.CefpycoHandle()
        self.cef_handle.begin(portnum=port)
        self.piece: Piece = piece

        self.name = name
        self.timeout_limit = timeout_limit
        self.rcv_tail_index = None
        self.req_tail_index = None
        self.req_flag = None
        self.pipeline = pipeline

        # test
        self.data_size = 0


    def run(self):
        _, end_chunk_num = self.get_first_chunk(self.name)
        if end_chunk_num is None:
            logging.error("failed to get_first_chunk")
            return
        info = CefAppRunningInfo(self.name, end_chunk_num)
        self.on_start(info)
        while info.timeout_count < self.timeout_limit and self.continues_to_run(info):
            packet = self.cef_handle.receive()
            if packet.is_failed:
                info.timeout_count += 1
                self.on_rcv_failed(info)
            elif packet.name == info.name:
                self.on_rcv_succeeded(info, packet)
        if info.num_of_finished == info.end_chunk_num:
            print("success download piece: {}".format(self.piece.piece_index))
            return True
        else:
            return False

    # return first_chunk_payload and end_chunk_num
    def get_first_chunk(self, name) -> (bytes, int):
        while True:
            self.cef_handle.send_interest(name, 0)
            packet = self.cef_handle.receive()
            if packet.is_failed:
                continue
            if packet.is_interest_return:
                continue
            if packet.name != name:
                continue
            self.data_size += packet.payload_len
            piece_index = int(packet.name.split('/')[-1])
            """pub.sendMessage('PiecesManager.Piece',
                            piece=(piece_index, 0, packet.payload))
            """
            self.piece.set_block(0, packet.payload)
            return packet.payload, packet.end_chunk_num

    def on_start(self, info):
        self.req_flag = np.zeros(info.end_chunk_num + 1)
        self.req_flag[0] = 1
        self.rcv_tail_index = 1
        self.req_tail_index = 1
        self.send_interests_with_pipeline(info)

    @staticmethod
    def continues_to_run(info):
        return 0 in info.finished_flag

    def on_rcv_failed(self, info):
        self.reset_req_status(info)
        self.send_interests_with_pipeline(info)

    def on_rcv_succeeded(self, info, packet):
        piece_index = int(packet.name.split('/')[-1])

        chunk_num = packet.chunk_num
        if info.finished_flag[chunk_num]: return
        self.piece.set_block(packet.payload_len * chunk_num, packet.payload)
        if self.piece.are_all_blocks_full():
            if self.piece.set_to_full():
                pass
        """pub.sendMessage('PiecesManager.Piece',
                        piece=(piece_index, packet.payload_len * chunk_num, packet.payload))
        """
        info.finished_flag[chunk_num] = 1
        info.num_of_finished += 1
        self.data_size += packet.payload_len

        self.send_next_interest(info)

    def reset_req_status(self, info):
        self.req_flag = np.zeros(info.end_chunk_num + 1)
        self.req_tail_index = self.rcv_tail_index
        while self.req_tail_index < info.end_chunk_num and info.finished_flag[self.req_tail_index]:
            self.req_tail_index += 1

    def send_interests_with_pipeline(self, info):
        to_index = min(info.end_chunk_num, self.req_tail_index + self.pipeline)
        for i in range(self.req_tail_index, to_index + 1):
            if info.finished_flag[i]:
                continue
            self.cef_handle.send_interest(info.name, i)
            self.req_flag[i] = 1

    def send_next_interest(self, info):
        while self.rcv_tail_index < info.end_chunk_num and info.finished_flag[self.rcv_tail_index]:
            self.rcv_tail_index += 1
        while (self.req_tail_index < info.end_chunk_num and
               (info.finished_flag[self.req_tail_index] or self.req_flag[self.req_tail_index])):
            self.req_tail_index += 1
        if self.req_tail_index < info.end_chunk_num:
            self.cef_handle.send_interest(info.name, self.req_tail_index)
            self.req_flag[self.req_tail_index] = 1
