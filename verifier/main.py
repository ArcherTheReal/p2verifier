import asyncio
from verifier.logger import log, vlog


def main():
    # This is the main function that will be called when the script is run
    asyncio.run(async_main())

async def async_main():
    # This is the main function that will be called when the script is run
    vlog("Hello, world!")