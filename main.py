#!/usr/bin/env python3
import subprocess

from src.global_value import com_manager
import src.global_value as gv
from src.application.interest_listener import InterestListener
from src.application.bittorrent.communication_manager import CommunicationManager

def main():
    res = subprocess.run(["cefnetdstart"], shell=True)

    com_manager = CommunicationManager()
    c_process = InterestListener()

    c_process.start()


if __name__ == '__main__':
    main()
