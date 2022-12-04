import os
from multiprocessing import Lock

threads = []
thread_flag = True
torrent_list = []
CACHE_PATH = os.environ['HOME']+"/proxy_cache/"
m_lock = Lock()
