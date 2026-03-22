import os, json, threading
import numpy as np, cv2, mss

def load_roi(path=os.path.join("assets", "boundaries.json")):
    with open(path, "r") as f:
        boundaries = json.load(f)

    seg_points = boundaries["annotations"][0]["segmentation"][0]
    ROI_POLYGON = np.array(list(zip(seg_points[0::2], seg_points[1::2])), dtype=np.int32)
    return ROI_POLYGON

# Load ROI + compute bounding rect
ROI_POLYGON = load_roi()
RX, RY, RW, RH = cv2.boundingRect(ROI_POLYGON)

ROI_POLY_LOCAL = ROI_POLYGON.copy()
ROI_POLY_LOCAL[:, 0] -= RX
ROI_POLY_LOCAL[:, 1] -= RY

ROI_DYNAMIC = None  # (x, y, w, h) in absolute screen coords

ROI_MASK = np.zeros((RH, RW), dtype=np.uint8)
cv2.fillPoly(ROI_MASK, [ROI_POLY_LOCAL.astype(np.int32)], 255)

MONITOR = {"left": RX, "top": RY, "width": RW, "height": RH}

_thread_ctx = threading.local()


ROI_LAST = None
ROI_FAILS = 0

def set_dynamic_roi(arena_bbox, pitch, margin_tiles=2, max_shift=0.2):
    global ROI_DYNAMIC, ROI_LAST, ROI_FAILS

    if arena_bbox is None:
        ROI_FAILS += 1
        if ROI_FAILS < 10 and ROI_LAST is not None:
            ROI_DYNAMIC = ROI_LAST  # reuse last
        else:
            ROI_DYNAMIC = None
        return

    ROI_FAILS = 0
    x, y, w, h = arena_bbox
    margin = margin_tiles * pitch
    new_roi = (x - margin, y - margin, w + 2*margin, h + 2*margin)

    # Smooth changes
    if ROI_LAST is not None:
        lx, ly, lw, lh = ROI_LAST
        if abs(new_roi[0]-lx) > max_shift*lw or abs(new_roi[1]-ly) > max_shift*lh:
            ROI_DYNAMIC = ROI_LAST  # ignore sudden jump
            return

    ROI_DYNAMIC = new_roi
    ROI_LAST = new_roi
    #print("[DEBUG] ROI_DYNAMIC set to", ROI_DYNAMIC)


def _get_sct():
    sct = getattr(_thread_ctx, "sct", None)
    if sct is None:
        _thread_ctx.sct = mss.mss()
        sct = _thread_ctx.sct
    return sct

def _grab_roi():
    """Grab BGRA numpy array of the ROI rectangle."""
    sct = _get_sct()
    if ROI_DYNAMIC is not None:
        dx, dy, dw, dh = ROI_DYNAMIC
        return np.array(sct.grab({"left": dx, "top": dy, "width": dw, "height": dh}))
    else:
        return np.array(sct.grab(MONITOR))

def apply_polygon_mask(frame, polygon_points):
    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    pts = np.array(polygon_points, dtype=np.int32)
    cv2.fillPoly(mask, [pts], 255)
    return cv2.bitwise_and(frame, frame, mask=mask)

def get_current_roi_origin():
    """Absolute screen origin of the current ROI grab."""
    from .roi import RX, RY, ROI_DYNAMIC  # or just use globals if in same file
    if ROI_DYNAMIC is None:
        return RX, RY
    dx, dy, _, _ = ROI_DYNAMIC
    return RX + dx, RY + dy

def roi_local_to_abs(pt):
    ox, oy = get_current_roi_origin()
    return (pt[0] + ox, pt[1] + oy)
