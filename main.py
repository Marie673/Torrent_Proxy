import time
from threading import Thread


class TestThread(Thread):
    def __init__(self):
        super().__init__()
        self.test = 0

    def run(self) -> None:
        pre_time = time.time()
        while True:
            now_time = time.time()
            if now_time - pre_time > 1:
                print(self.test)
                pre_time = time.time()

    def add_test(self):
        self.test += 1


def main():
    t = TestThread()
    t.start()

    for _ in range(5):
        time.sleep(2)
        t.add_test()


if __name__ == '__main__':
    main()
