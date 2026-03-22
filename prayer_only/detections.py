import time, cv2, numpy as np, threading
from vardorvis.roi import _grab_roi, ROI_MASK, ROI_DYNAMIC, RX, RY, get_current_roi_origin
from vardorvis.debug import draw_detections, should_take_snapshot, FpsCounter

ROI_MISS_COUNTER = 0
ROI_MISS_MAX = 10

_latest_detection = None
_latest_full_detection = None
latest_frame = None
_latest_lock = threading.RLock()

def get_blue_tile_detections(debug=False):
    global ROI_DYNAMIC, ROI_MISS_COUNTER
    frame = _grab_roi()
    ORX, ORY = get_current_roi_origin()

    if ROI_DYNAMIC is None and ROI_MASK is not None:
        if ROI_MASK.shape[:2] == frame.shape[:2]:
            frame = cv2.bitwise_and(frame, frame, mask=ROI_MASK)

    # --- color thresholding just for blue ---
    lower_blue = np.array([200, 0, 0, 128], dtype=np.uint8)
    upper_blue = np.array([255, 60, 60, 255], dtype=np.uint8)
    blue_mask  = cv2.inRange(frame, lower_blue, upper_blue)

    blue_rects = [cv2.boundingRect(c)
                  for c in cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]]
    blue_squares = [{"rect": (x+ORX, y+ORY, w, h)}
                    for (x,y,w,h) in blue_rects if w*h > 1000]

    if debug:
        dbg = frame.copy()
        for sq in blue_squares:
            x, y, w, h = sq["rect"]
            cv2.rectangle(dbg, (x, y), (x+w, y+h), (255,0,0,255), 2)
        cv2.imwrite("debug/blue_debug.png", dbg)

    return {
        "blue_squares": blue_squares,
        "blue_tile": bool(blue_squares),
        "frame": frame,
        "roi_origin": (ORX, ORY),
    }

def detection_loop(metronome):
    global _latest_detection, _latest_full_detection, latest_frame
    polls_per_tick = 12
    poll_delay = metronome.tick_interval / polls_per_tick
    fps_counter = FpsCounter("detection_loop")

    while True:
        metronome.wait_for_next_tick()
        for _ in range(polls_per_tick):
            latest = get_blue_tile_detections(debug=False)
            if not latest:
                time.sleep(poll_delay)
                continue

            reduced = {
                "blue_tile": latest.get("blue_tile", False),
                "blue_squares": latest.get("blue_squares", []),
                "roi_origin": latest.get("roi_origin", (RX, RY)),
            }

            with _latest_lock:
                _latest_detection = reduced
                _latest_full_detection = latest
                latest_frame = latest.get("frame", None)

                if should_take_snapshot() and latest_frame is not None:
                    ts = int(time.time() * 1000)
                    draw_detections(
                        latest_frame,
                        {**latest, **reduced},
                        save_path=f"debug/overlay_{ts}.png",
                        origin=reduced.get("roi_origin", (0, 0))
                    )

            fps_counter.tick()
            time.sleep(poll_delay)

def get_latest_blue_detections():
    with _latest_lock:
        return dict(_latest_detection) if _latest_detection else None
