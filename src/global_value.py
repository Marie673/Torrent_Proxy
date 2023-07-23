from multiprocessing import Lock
import datetime
import os

CHUNK_SIZE = 1024 * 4
CACHE_PATH = os.environ["HOME"] + "/proxy_cache/"
MAX_PEER_CONNECT = 1
EVALUATION = True
EVALUATION_PATH = os.environ["HOME"] + "/evaluation/proxy/test"

TORRENT_FILE_PATH = os.environ["HOME"] + "/torrent/"

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
