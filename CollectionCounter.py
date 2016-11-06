import threading
import time


class CollectionCounter:
    """Thread-safe class to keep count of the amount of players collected and print the average collection rate.
    """
    lock = threading.Lock()

    def __init__(self, print_freq: int = 1):
        self.count = 0
        self.timeStarted = time.time() - 1  # So we don't get ZeroDivisionError
        self.print_freq = print_freq
        self.collected_last_second = 0
        self.print_collection_rate()  # An explicit timer would be better, I'll change this later maybe.

    def increment(self, amount: int):
        with self.lock:
            self.count += amount

        self.collected_last_second += amount

    def print_collection_rate(self):
        threading.Timer(self.print_freq, self.print_collection_rate).start()

        print("Average collection rate: {}/sec".format(int(self.count / (time.time() - self.timeStarted))))
        print("{} seconds since start".format(int(time.time() - self.timeStarted)))
        print("{} Collected last second.".format(self.collected_last_second))
        self.collected_last_second = 0