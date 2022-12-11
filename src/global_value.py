from multiprocessing import Lock
import datetime

CHUNK_SIZE = 1024 * 4
CACHE_PATH = "/proxy/proxy_cache/"
MAX_PEER_CONNECT = 1
EVALUATION = True
EVALUATION_PATH = "/proxy/evaluation/proxy/test"

threads = []
thread_flag = True
torrent_list = []
m_lock = Lock()


def log(msg):
    if not EVALUATION:
        return
    msg = str(datetime.datetime.now()) + ", " + msg + "\n"
    with open(EVALUATION_PATH, "a+") as file:
        file.write(msg)
