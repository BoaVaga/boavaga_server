from datetime import time


def time_from_total_seconds(seconds: int):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    return time(hour=hours, minute=minutes, second=seconds)
