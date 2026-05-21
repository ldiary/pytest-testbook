__version__ = '1.2.6'

import warnings
import sys
import asyncio
import threading
import queue
from playwright.sync_api import sync_playwright

task_queue = queue.Queue()
pw_state = {}
error_state = {'error': None}
_worker_thread = None


# 1. Add the headless parameter here
def _playwright_worker(headless=True):
    if sys.platform == 'win32':
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    pw = sync_playwright().start()

    # 2. Pass it to the chromium launch command
    browser = pw.chromium.launch(headless=headless)

    context = browser.new_context(locale='en-US', timezone_id='America/New_York')
    page = context.new_page()

    pw_state.update({'pw': pw, 'browser': browser, 'context': context, 'page': page})

    while True:
        task = task_queue.get()
        if task is None:
            break
        try:
            task(pw_state)
        except Exception as e:
            error_state['error'] = e
        task_queue.task_done()

    browser.close()
    pw.stop()


# 3. Add the parameter to your public function with True as default
def pw_start(headless=True):
    """Starts the Playwright thread if it isn't already running."""
    global _worker_thread
    if _worker_thread is None or not _worker_thread.is_alive():
        # 4. Use kwargs to pass the argument into the thread's target function
        _worker_thread = threading.Thread(
            target=_playwright_worker,
            kwargs={'headless': headless},
            daemon=True
        )
        _worker_thread.start()


def pw_stop():
    """Gracefully shuts down the Playwright thread."""
    global _worker_thread
    if _worker_thread is not None and _worker_thread.is_alive():
        task_queue.put(None)
        _worker_thread.join(timeout=5)
        _worker_thread = None


def pw_execute(func):
    """Sends a task to the background Playwright thread."""
    error_state['error'] = None
    task_queue.put(func)
    task_queue.join()
    if error_state['error']:
        raise error_state['error']