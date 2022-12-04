import os
from multiprocessing import Lock

threads = []
torrent_list = []
CACHE_PATH = os.environ['HOME']+"/proxy_cache/"
m_lock = Lock()
