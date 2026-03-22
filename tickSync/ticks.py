import time
import threading
from vardorvis.tick_sync import sync_tick_clock_once

class TickMetronome:
    """
    Runs a background metronome synchronized to the in-game tick clock.
    """
    def __init__(self, tick_interval=0.6):
        self.tick_interval = tick_interval
        self.phase_offset = 0.0
        self.lock = threading.Lock()
        self.last_tick_time = time.time()
        self._stop = False

        threading.Thread(target=self._run, daemon=True).start()
        threading.Thread(target=self._resync_loop, daemon=True).start()

    def _run(self):
        while not self._stop:
            with self.lock:
                interval = self.tick_interval
                offset = self.phase_offset
            now = time.time()
            # Adjust next tick if just started or after resync
            next_tick_time = now + offset
            while not self._stop:
                now = time.time()
                sleep_time = next_tick_time - now
                if sleep_time > 0:
                    time.sleep(sleep_time)
                self.last_tick_time = time.time()
                next_tick_time += interval

    def _resync_loop(self):
        while not self._stop:
            tick_events = sync_tick_clock_once()
            if len(tick_events) == 3:
                tick_events_sorted = sorted(tick_events, key=lambda x: x[1])
                times = [t for t, _ in tick_events_sorted]
                offset = times[0] - time.time()
                with self.lock:
                    self.phase_offset = offset
            time.sleep(5)

    def wait_for_next_tick(self):
        last = self.get_last_tick_time()
        while True:
            now = self.get_last_tick_time()
            if now > last:
                return now
            time.sleep(0.001)

    def get_last_tick_time(self):
        return self.last_tick_time

    def stop(self):
        self._stop = True
