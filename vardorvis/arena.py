import cv2
import numpy as np

def find_arena_box(frame_bgra, debug=False, tag="arena"):
    """
    Detect teal corner boxes in the arena.
    Returns pitch (tile size), bounding boxes for teal corners.
    """
    # --- Convert to HSV for robust color detection ---
    hsv = cv2.cvtColor(cv2.cvtColor(frame_bgra, cv2.COLOR_BGRA2BGR), cv2.COLOR_BGR2HSV)

    # Teal color mask (tune as needed)
    lower_teal = np.array([35, 150, 150], dtype=np.uint8)
    upper_teal = np.array([95, 255, 255], dtype=np.uint8)
    mask = cv2.inRange(hsv, lower_teal, upper_teal)

    # Find contours of teal boxes
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    corner_boxes = []
    pitches = []

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        area = w * h
        aspect = w / float(h) if h > 0 else 0

        # Strict filtering: must be square and within reasonable size
        if area < 8000:  # too small → noise
            continue
        if aspect < 0.85 or aspect > 1.15:  # enforce squareness
            continue

        corner_boxes.append((x, y, w, h))
        pitches.append(int((w + h) // 2))

    if not corner_boxes:
        return None

    # Estimate pitch from median size of detected teal squares
    pitch = int(np.median(pitches))

    if debug:
        dbg = frame_bgra.copy()
        for (x, y, w, h) in corner_boxes:
            cv2.rectangle(dbg, (x, y), (x + w, y + h), (0, 255, 255, 255), 2)  # yellow corners
        cv2.imwrite(f"debug/{tag}_mask.png", mask)
        cv2.imwrite(f"debug/{tag}_arena_box.png", dbg)

    return {
        "corner_boxes": corner_boxes,
        "pitch": pitch
    }


def get_arena_box(frame_bgra, screen_center=(1900, 1060), arena_tiles=11, debug=False):
    """
    Use detected teal boxes to infer arena bbox.
    Expands dynamically if fewer than 4 corners are visible.
    """
    result = find_arena_box(frame_bgra, debug=debug, tag="arena")
    if not result:
        return None

    corners = result["corner_boxes"]
    pitch = result["pitch"]
    arena_size = arena_tiles * pitch

    if len(corners) >= 4:
        xs = [x for x, _, w, _ in corners] + [x + w for x, _, w, _ in corners]
        ys = [y for _, y, _, h in corners] + [y + h for _, y, _, h in corners]
        bbox = (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))

    elif len(corners) == 2:
        (x1, y1, w1, h1), (x2, y2, w2, h2) = corners
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2

        if abs(x1 - x2) < pitch * 2:
            y = int(cy - arena_size // 2)
            h = arena_size
            if cx <= screen_center[0]:
                x = min(x1, x2)
                w = arena_size
            else:
                w = arena_size
                x = max(x1, x2) - w - int(pitch * 2)
        elif abs(y1 - y2) < pitch * 2:
            x = int(cx - arena_size // 2)
            w = arena_size
            if cy <= screen_center[1]:
                y = min(y1, y2)
                h = arena_size
            else:
                h = arena_size
                y = max(y1, y2) - h - int(pitch * 2)
        else:
            x = int(cx - arena_size // 2)
            y = int(cy - arena_size // 2)
            w = h = arena_size
        bbox = (x, y, w, h)

    elif len(corners) == 3:
        xs = [x for x, _, w, _ in corners] + [x + w for x, _, w, _ in corners]
        ys = [y for _, y, _, h in corners] + [y + h for _, y, _, h in corners]
        bbox = (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))

    else:
        return None

    if debug:
        dbg = frame_bgra.copy()
        for (x, y, w, h) in corners:
            cv2.rectangle(dbg, (x, y), (x + w, y + h), (0, 255, 255, 255), 2)
        cv2.rectangle(dbg, (bbox[0], bbox[1]),
                      (bbox[0] + bbox[2], bbox[1] + bbox[3]),
                      (255, 0, 255, 255), 2)  # magenta arena box
        cv2.imwrite("debug/arena_bbox.png", dbg)

    return {"bbox": bbox, "pitch": pitch, "corners": corners}
