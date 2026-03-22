import pyautogui
import queue
import time
import itertools

# PriorityQueue: lower number = higher priority
mouse_action_queue = queue.PriorityQueue()
_action_counter = itertools.count()  # tie-breaker


def queue_mouse_action(func, *args, priority=0, **kwargs):
    count = next(_action_counter)

    # Normalize to absolute for pyautogui
    if func is pyautogui.leftClick:
        if len(args) == 2:
            kwargs["x"], kwargs["y"] = args
            args = ()
            print(f"[DEBUG] Executing {func.__name__} with args={args}, kwargs={kwargs}")
    elif func is pyautogui.moveTo:
        if len(args) == 2:
            kwargs["x"], kwargs["y"] = args
            args = ()
        kwargs["duration"] = 0
    
    mouse_action_queue.put((priority, count, func, args, kwargs))


def queue_keyboard_action(func, *args, priority=0, **kwargs):
    """
    Queue a keyboard action.
    Default priority = 0 (same as clicks).
    """
    count = next(_action_counter)
    mouse_action_queue.put((priority, count, func, args, kwargs))


def mouse_action_worker():
    while True:
        priority, count, func, args, kwargs = mouse_action_queue.get()
        try:
            func(*args, **kwargs)
        finally:
            mouse_action_queue.task_done()
        time.sleep(0.001)


def shift_click(x, y, button="left", priority=10):
    """
    Perform a shift+click at (x,y).
    Always queued at low priority unless explicitly overridden.
    """
    def _shift_click_action(x, y, button="left"):
        pyautogui.keyDown("shift")
        try:
            pyautogui.click(x=x, y=y, button=button)
        finally:
            pyautogui.keyUp("shift")

    count = next(_action_counter)
    mouse_action_queue.put((priority, count, _shift_click_action, (x, y), {"button": button}))
