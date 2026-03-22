import time, cv2
from vardorvis.roi import _grab_roi, RX, RY

class TickClockSync:
    def __init__(self, region=(910,1630,245,80), debug=False, poll_interval=0.01):
        self.region = region
        self.debug = debug
        self.poll_interval = poll_interval

    def __iter__(self):
        return self._iterate()

    def _iterate(self):
        last_phase = None
        while True:
            circles = self.get_circles()
            if len(circles) == 3:
                yellow_idx = next((i for i,c in enumerate(circles) if c['color']=='yellow'), None)
                if yellow_idx is not None and yellow_idx != last_phase:
                    last_phase = yellow_idx
                    yield (time.time(), yellow_idx)
            time.sleep(self.poll_interval)

    def get_circles(self):
        full = _grab_roi()
        rx, ry, rw, rh = self.region
        x0 = max(0, rx - RX)
        y0 = max(0, ry - RY)
        sub = full[y0:y0+rh, x0:x0+rw]

        img_bgr = cv2.cvtColor(sub[...,:3], cv2.COLOR_BGRA2BGR)
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        blurred = cv2.medianBlur(gray, 5)
        circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1.2, minDist=40,
                                   param1=50, param2=30, minRadius=15, maxRadius=40)
        results = []
        if circles is not None:
            for (x,y,r) in circles[0].round().astype("int"):
                bgr = img_bgr[y, x]
                if bgr[2]>180 and bgr[1]>180 and bgr[0]<100: color='yellow'
                elif all(c<80 for c in bgr): color='black'
                else: color='other'
                results.append({'center': (x+RX, y+RY), 'radius': r, 'color': color})
        return results

def sync_tick_clock_once(wait_time=5.0):
    sync = TickClockSync()
    seen_phases, tick_events = set(), []
    for tick_time, phase in sync:
        if phase not in seen_phases:
            seen_phases.add(phase)
            tick_events.append((tick_time, phase))
        if len(seen_phases) == 3:
            break
    time.sleep(wait_time)
    return tick_events
