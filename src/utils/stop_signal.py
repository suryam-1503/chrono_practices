import threading

stop_event = threading.Event()

def stop_automation():
    stop_event.set()

def reset_stop():
    stop_event.clear()

def check_stop_flag():
    return stop_event.is_set()