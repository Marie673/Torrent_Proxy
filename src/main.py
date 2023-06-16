import global_value
from src.application.interest_listener import InterestListener
from src.application.bittorrent.communication_manager import CommunicationManager


com_manager = None


def main():
    global com_manager
    com_manager = CommunicationManager()
    c_process = InterestListener()

    c_process.start()


if __name__ == '__main__':
    main()
