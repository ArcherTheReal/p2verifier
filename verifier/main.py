import asyncio
from verifier.logger import log

class Verifier:
    def __init__(self):
        self.config = None
        self.output = {}
        self.run = ""
        self.mdp = ""
        self.p2demos = ""
        self.demoFilenames = []
        self.demos = {}
        self.demoToMap = {}
        self.serverNumbers = {}
        self.reader = None
        self.writer = None
        self.portal2Process = None

verifier = Verifier()


def main():
    # This is the main function that will be called when the script is run
    asyncio.run(async_main())

async def async_main():
    # This is the main function that will be called when the script is run
    log("Hello, world!")
    log("Hello, world!")