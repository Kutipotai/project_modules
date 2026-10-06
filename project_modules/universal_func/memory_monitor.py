import psutil
import os
import time
import threading
import gc

class MemoryMonitor:
    def __init__(self, interval=0.05):
        self.interval = interval
        self.peak = 0
        self.running = False
        self.process = psutil.Process(os.getpid())

    def _monitor(self):
        while self.running:
            mem = self.process.memory_info().rss
            if mem > self.peak:
                self.peak = mem
            time.sleep(self.interval)

    def start(self):
        gc.collect()
        self.peak = self.process.memory_info().rss
        self.running = True
        self.thread = threading.Thread(target=self._monitor, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()
        gc.collect()
        return self.peak / (1024 ** 2)  # возвращаем в МБ

