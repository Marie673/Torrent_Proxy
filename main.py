#!/usr/bin/env python3
import asyncio

from src.application.interest_listener import InterestListener
from logger import logger

def main():
    logger.debug("start")
    c_process = InterestListener()
    asyncio.run(c_process.run())


if __name__ == '__main__':
    main()
