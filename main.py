#!/usr/bin/env python3
import subprocess

from src.application.interest_listener import InterestListener


def main():
    res = subprocess.run(["cefnetdstart"], shell=True)

    c_process = InterestListener()

    c_process.start()


if __name__ == '__main__':
    main()
