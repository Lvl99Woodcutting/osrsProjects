import threading
import keyboard
import time
from vardorvis.ticks import TickMetronome
from vardorvis.detections import detection_loop, get_latest_blue_detections
from vardorvis.inputs import mouse_action_worker
from vardorvis.logic_vardorvis import blue_flag_reset_loop, process_prayer_switch
from vardorvis.debug import request_screenshot


stop_script = False


def esc_handler():
    global stop_script
    print("Escape pressed, exiting script.")
    stop_script = True


_stop_event = threading.Event()

def _hotkey_worker():
    print("[DEBUG] Hotkeys: F9 = save debug overlay, ESC = exit")
    while not _stop_event.is_set():
        try:
            if keyboard.is_pressed("f9"):
                request_screenshot()     # now from debug.py
                time.sleep(0.25)         # de-bounce
            if keyboard.is_pressed("esc"):
                _stop_event.set()
                print("Escape pressed, exiting script.")
                break
        except RuntimeError:
            pass
        time.sleep(0.02)


keyboard.add_hotkey("esc", esc_handler)

if __name__ == "__main__":
    metronome = TickMetronome()

    # Start background workers
    threading.Thread(target=detection_loop, args=(metronome,), daemon=True).start()
    threading.Thread(target=mouse_action_worker, daemon=True).start()
    threading.Thread(target=blue_flag_reset_loop, daemon=True).start()
    threading.Thread(target=_hotkey_worker, daemon=True).start()

    print("[DEBUG] Script started. Waiting for detections...")

    try:
        while not stop_script:
            metronome.wait_for_next_tick()
            detection = get_latest_blue_detections()

            if detection is not None and detection.get("blue_tile"):
                threading.Thread(target=process_prayer_switch, args=(True,), daemon=True).start()

    finally:
        metronome.stop()
