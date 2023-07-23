#!/usr/bin/env python3
import asyncio

from src.application.interest_listener import InterestListener


def main():
    c_process = InterestListener()
    asyncio.run(c_process.run())


if __name__ == '__main__':
    main()
