# playwright_shutdown.py
try:
    if 'task_queue' in globals() and 'worker_thread' in globals():
        task_queue.put(None)
        worker_thread.join(timeout=5)
except Exception:
    pass