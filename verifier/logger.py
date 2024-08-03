import datetime
from verifier.colors import Colors

def log(message):
    """
    Logs a message with a timestamp, using blue for the timestamp and green for the message.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{Colors.colorize(timestamp, Colors.BLUE)}] {Colors.colorize(message, Colors.GREEN)}")
