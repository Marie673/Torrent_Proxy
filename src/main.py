import global_value
import application.bittorrent as bittorrent
import application.interest_listener as listener


def main():
    b_process = bittorrent()
    c_process = listener()

    b_process.start()
    c_process.start()


if __name__ == '__main__':
    main()
