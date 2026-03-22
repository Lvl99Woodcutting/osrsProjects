import time
import threading
import pyautogui
from vardorvis.ticks import TickMetronome
from vardorvis.detections import get_latest_blue_detections
from vardorvis.inputs import queue_mouse_action, queue_keyboard_action, shift_click

# State flags
head_react_running = False
blue_flag_lock = threading.Lock()
blue_active_flag = False

def process_prayer_switch(blue_tile):
    if not blue_tile:
        return
    global head_react_running, blue_active_flag

    with blue_flag_lock:
        if head_react_running or not blue_active_flag:
            return
    
    head_react_running = True
    blue_active_flag = False  # Reset flag immediately to avoid repeated triggers
    try:
        if blue_tile:
            metronome = TickMetronome()
            mouse_x, mouse_y = pyautogui.position()
            queue_keyboard_action(pyautogui.press, 'f2') # Switch to prayer tab
            time.sleep(0.06)
            queue_mouse_action(pyautogui.leftClick, 3560, 1710)
            queue_mouse_action(pyautogui.moveTo, mouse_x, mouse_y)
            time.sleep(0.01)
            queue_keyboard_action(pyautogui.press, 'f1') # Switch back to inventory tab
            # Wait for the next tick before the final click
            metronome.wait_for_next_tick()
            metronome.wait_for_next_tick()
            mouse_x, mouse_y = pyautogui.position()
            queue_keyboard_action(pyautogui.press, 'f2') # Switch to prayer tab
            time.sleep(0.06)
            queue_mouse_action(pyautogui.leftClick, 3640, 1710)
            queue_mouse_action(pyautogui.moveTo, mouse_x, mouse_y)
            time.sleep(0.01)
            queue_keyboard_action(pyautogui.press, 'f1') # Switch back to inventory tab
            time.sleep(0.6)
    finally:
        head_react_running = False


def blue_flag_reset_loop(poll_delay=0.05):
    global blue_active_flag
    while True:
        detection = get_latest_blue_detections()
        blue_tile = detection['blue_tile'] if detection else False

        with blue_flag_lock:
            if blue_tile and not blue_active_flag:
                #print("[DEBUG] Blue square detected, flag set.")
                blue_active_flag = True
            elif not blue_tile and blue_active_flag:
                #print("[DEBUG] Blue square gone, resetting flag.")
                blue_active_flag = False

        time.sleep(poll_delay)
