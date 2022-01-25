import sys
import time
import numpy as np
import cefpyco
from sys import stderr

NAME0='ccnx:/test/1M.dummy'
NAME1='ccnx:/test/10M.dummy'
NAME2='ccnx:/test/100M.dummy'


MAX_INTEREST = 1000
BLOCK_SIZE = 30

class CefAppRunningInfo(object):
    def __init__(self, name, count):
        self.name = name
        self.count = count
        self.n_finished = 0
        self.finished_flag = np.zeros(count)
        self.timeout_count = 0

class MetaInfoNotResolvedError(Exception):
    pass

class CefApp(object):
    def __init__(self, cef_handle, target_name, action_name, timeout_limit):
        self.cef_handle = cef_handle
        self.target_name = target_name
        self.action_name = action_name
        self.timeout_limit = timeout_limit

    def run(self, name, count=0):
        if count <= 0:
            count = self.resolve_count(name)
            if not count:
                errmsg = "{0}/meta is not resolved.".format(name)
                raise MetaInfoNotResolvedError(errmsg)

        info = CefAppRunningInfo(name, count)
        self.on_start(info)
        while info.timeout_count < self.timeout_limit and self.continues_to_run(info):
            packet = self.cef_handle.receive()
            if packet.is_failed:
                info.timeout_count += 1
                self.on_rcv_failed(info)
            elif packet.name == info.name:
                self.on_rcv_succeeded(info, packet)
        if info.n_finished == info.count:
            self.show_result_on_success(info)
        else:
            self.show_result_on_failure(info)

    def resolve_count(self, name):
        raise NotImplementedError()

    def on_start(self, info):
        pass

    def on_rcv_failed(self, info):
        pass

    def on_rcv_succeeded(self, info, packet):
        pass

    def on_rcv_meta(self, info, packet):
        pass

    def continues_to_run(self, info):
        raise NotImplementedError()

    def show_result_on_success(self, info):
        pass

    def show_result_on_failure(self, info):
        buf = ""
        last = -2
        seq = False
        miss_count = 0
        for i in range(info.count):
            if info.finished_flag[i]:
                continue
            miss_count += 1
            if last == i - 1:
                if not seq:
                    buf += "--"
                seq = True
            else:
                if seq:
                    buf += "#{0}, #{1}".format(last, i)
                else:
                    sep = ", " if last >= 0 else ""
                    buf += "{0}#{1}".format(sep, i)
                seq = False
            last = i
        if seq:
            buf += "#{0}".format(last)


class CefAppConsumer(CefApp):
    def __init__(self, cef_handle,
                 pipeline=1000, timeout_limit=2, data_store=True):
        self.rcv_tail_index = None
        self.req_tail_index = None
        self.cob_list = None
        self.req_flag = None
        self.pipeline = pipeline
        self.data_store = data_store
        super(CefAppConsumer, self).__init__(
            cef_handle, "Data", "receive", timeout_limit)

    @property
    def data(self):
        return "".join(self.cob_list) if self.data_store else None

    def resolve_count(self, name):
        for i in range(self.timeout_limit):
            self.cef_handle.send_interest(name, 0)
            packet = self.cef_handle.receive()
            if packet.is_failed: continue
            if packet.is_interest_return:
                continue
            if packet.name != name: continue
            return int(packet.end_chunk_num)
        return None

    def on_start(self, info):
        self.req_flag = np.zeros(info.count)
        if self.data_store: self.cob_list = [""] * info.count
        self.rcv_tail_index = 0
        self.req_tail_index = 0
        self.send_interests_with_pipeline(info)

    def continues_to_run(self, info):
        return info.n_finished < info.count

    def on_rcv_failed(self, info):
        self.reset_req_status(info)
        self.send_interests_with_pipeline(info)

    def on_rcv_succeeded(self, info, packet):
        c = packet.chunk_num
        if info.finished_flag[c]: return
        if self.data_store: self.cob_list[c] = packet.payload_s
        info.finished_flag[c] = 1
        info.n_finished += 1
        self.send_next_interest(info)

    def reset_req_status(self, info):
        self.req_flag = np.zeros(info.count)
        self.req_tail_index = self.rcv_tail_index
        while self.req_tail_index < info.count and info.finished_flag[self.req_tail_index]:
            self.req_tail_index += 1

    def send_interests_with_pipeline(self, info):
        to_index = min(info.count, self.req_tail_index + self.pipeline)
        for i in range(self.req_tail_index, to_index):
            if info.finished_flag[i]: continue
            self.cef_handle.send_interest(info.name, i)
            self.req_flag[i] = 1

    def send_next_interest(self, info):
        while self.rcv_tail_index < info.count and info.finished_flag[self.rcv_tail_index]:
            self.rcv_tail_index += 1
        while (self.req_tail_index < info.count and
               (info.finished_flag[self.req_tail_index] or self.req_flag[self.req_tail_index])):
            self.req_tail_index += 1
        if self.req_tail_index < info.count:
            self.cef_handle.send_interest(info.name, self.req_tail_index)
            self.req_flag[self.req_tail_index] = 1


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

    with cefpyco.create_handle() as h:
        app = CefAppConsumer(
            h
        )
        try:
            start_time = time.time()
            app.run(name)
            end_time = time.time() - start_time
            print("time: {}".format(end_time))
        except MetaInfoNotResolvedError as e:
            return



if __name__ == '__main__':
    main()