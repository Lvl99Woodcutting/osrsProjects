
GRID_SIZE = 11
CENTER_IDX = GRID_SIZE // 2
HOME_IDX, ALT_IDX, SAFE_IDX = (0,5), (2,3), (2,7)
X_OFFSET = 50

AXE_CENTERS = {
    "left_top": (1,1),
    "left_middle": (1,5),
    "left_bottom": (1,9),
    "right_top": (9,1),
    "right_middle": (9,5),
    "right_bottom": (9,9),
}

def grid_index_to_px(arena_center, pitch, col, row):
    cx, cy = arena_center
    dx = (col - CENTER_IDX) * pitch
    dy = (row - CENTER_IDX) * pitch
    return (int(round(cx + dx)) + X_OFFSET, int(round(cy + dy)))

def infer_tiles_from_arena(arena_bbox):
    """
    Infer tile positions from arena bounding box.
    Assumes 11x11 grid, home at (0,5), alt at (2,3), safe at (2,7).
    """
    if arena_bbox is None:
        return None, None, None, None  # include pitch too

    x, y, w, h = arena_bbox
    pitch_x = w / (GRID_SIZE - 1)
    pitch_y = h / (GRID_SIZE - 1)
    pitch = int(round((pitch_x + pitch_y) / 2))  # average pitch
    arena_center = (x + w // 2, y + h // 2)

    home = grid_index_to_px(arena_center, pitch, *HOME_IDX)
    alt  = grid_index_to_px(arena_center, pitch, *ALT_IDX)
    safe = grid_index_to_px(arena_center, pitch, *SAFE_IDX)

    return home, alt, safe, pitch

def snap_abs_to_index(pt_abs, arena_center_abs, pitch):
    ax = (pt_abs[0] - arena_center_abs[0]) / float(pitch) + CENTER_IDX
    ay = (pt_abs[1] - arena_center_abs[1]) / float(pitch) + CENTER_IDX
    return int(round(ax)), int(round(ay))

def regions_from_purple_centers(purple_centers, arena_center_abs, pitch):
    region_bools = {
        "left_top": False, "left_middle": False, "left_bottom": False,
        "right_top": False, "right_middle": False, "right_bottom": False,
        "middle_top": False, "middle_bottom": False,
    }
    labeled = []
    if arena_center_abs is None or pitch is None:
        return labeled, region_bools

    for c_abs in purple_centers:
        col,row = snap_abs_to_index(c_abs, arena_center_abs, pitch)
        for label, (cx,cy) in AXE_CENTERS.items():
            if col == cx and row == cy:
                region_bools[label] = True
                labeled.append({"center": c_abs, "zone": label})
                break
    return labeled, region_bools
