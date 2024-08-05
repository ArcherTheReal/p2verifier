import datetime
from verifier.colors import Colors

def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{Colors.colorize(timestamp, Colors.BLUE)}] {Colors.colorize(message, Colors.ORANGE)}")

def error(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{Colors.colorize(timestamp, Colors.BLUE)}] {Colors.colorize(message, Colors.RED)}")