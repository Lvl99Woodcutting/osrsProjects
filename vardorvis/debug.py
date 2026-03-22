import os, cv2, time, threading

# --- Snapshot control (used by detection_loop) ---
_snapshot_event = threading.Event()

def request_screenshot():
    """Flag the detection loop to save one labeled overlay on the next poll."""
    _snapshot_event.set()

def should_take_snapshot():
    """Check & consume the snapshot flag."""
    if _snapshot_event.is_set():
        _snapshot_event.clear()
        return True
    return False


# --- FPS counter for polling/debug ---
class FpsCounter:
    def __init__(self, label="loop", interval=1.0):
        self.label = label
        self.interval = interval
        self._last_time = time.time()
        self._frame_count = 0

    def tick(self):
        """Call this once per frame/poll. Prints Hz every interval seconds."""
        self._frame_count += 1
        now = time.time()
        elapsed = now - self._last_time
        if elapsed >= self.interval:
            hz = self._frame_count / elapsed
            #print(f"[DEBUG] {self.label} running at {hz:.2f} Hz")
            self._last_time = now
            self._frame_count = 0


# --- Overlay drawing ---
def draw_detections(frame_bgra, det, save_path=None, origin=(0, 0), show=False):
    """
    Draw overlay on ROI-local frame with detections.

    Args:
        frame_bgra: BGRA numpy array (ROI-local)
        det: detection dict
        save_path: file path; if None, auto-names with timestamp
        origin: (RX, RY) so ABS coords align to this ROI frame
        show: if True, open cv2.imshow for live preview
    """
    ox, oy = origin
    canvas = frame_bgra.copy()

    def L(pt):  # ABS -> ROI-local
        return (int(pt[0] - ox), int(pt[1] - oy))

    def LR(rect):  # ABS rect -> ROI-local rect
        x, y, w, h = rect
        return (int(x - ox), int(y - oy), int(w), int(h))

    # Arena edges/corners
    box = det.get("arena_box") or {}
    for _, (x1, y1, x2, y2) in (box.get("lines") or {}).items():
        cv2.line(canvas, L((x1, y1)), L((x2, y2)), (255, 255, 0, 255), 2)
    for c in box.get("corners", []):
        cv2.circle(canvas, L(c), 5, (0, 255, 255, 255), -1)

    # Tile centers
    tc = det.get("tile_centers") or {}
    for key, col in [
        ("home_tile", (255, 255, 255, 255)),
        ("alt_tile",  (255, 255,   0, 255)),
        ("safe_tile", (  0, 255, 255, 255)),
    ]:
        pt = tc.get(key)
        if pt:
            P = L(pt)
            cv2.circle(canvas, P, 8, col, -1)
            cv2.putText(canvas, key.split("_")[0].upper(),
                        (P[0] + 10, P[1] - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, col, 2, cv2.LINE_AA)

    # Purple squares + labeled zones
    for sq in det.get("purple_squares", []):
        x, y, w, h = LR(sq["rect"])
        cv2.rectangle(canvas, (x, y), (x + w, y + h), (200, 0, 200, 255), 2)
    for p in det.get("regions_with_purple", []):
        C = L(p["center"])
        cv2.circle(canvas, C, 5, (200, 0, 200, 255), -1)
        cv2.putText(canvas, p.get("zone", "?"),
                    (C[0] + 8, C[1] - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 0, 200, 255), 1, cv2.LINE_AA)

    # Blue / Yellow / Red boxes
    for sq in det.get("blue_squares", []):
        x, y, w, h = LR(sq["rect"])
        cv2.rectangle(canvas, (x, y), (x + w, y + h), (255, 0, 0, 255), 2)
    for sq in det.get("yellow_squares", []):
        x, y, w, h = LR(sq["rect"])
        cv2.rectangle(canvas, (x, y), (x + w, y + h), (0, 255, 255, 255), 2)

    # Footer text
    debug_text = (
        f"HOME/ALT/SAFE dots; Purple/Blue/Yellow/Red boxes; cyan lines = arena | "
        f"Pitch={det.get('grid',{}).get('pitch')} | "
        f"Time={time.strftime('%H:%M:%S')}"
    )
    cv2.putText(canvas, debug_text, (12, 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255, 255),
                1, cv2.LINE_AA)

    # Save
    if save_path is None:
        os.makedirs("debug", exist_ok=True)
        ts = int(time.time() * 1000)
        save_path = f"debug/overlay_{ts}.png"
    cv2.imwrite(save_path, canvas)
    print(f"[DEBUG] wrote debug overlay -> {save_path}")

    if show:
        cv2.imshow("debug overlay", canvas)
        cv2.waitKey(1)

    return save_path
