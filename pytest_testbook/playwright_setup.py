import warnings
import sys
import asyncio
import threading
import queue
from playwright.sync_api import sync_playwright

task_queue = queue.Queue()
pw_state = {}
error_state = {'error': None}

def playwright_worker():
    if sys.platform == 'win32':
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)

    context = browser.new_context(
        locale='en-US',
        timezone_id='America/New_York'
    )
    page = context.new_page()

    pw_state['pw'] = pw
    pw_state['browser'] = browser
    pw_state['context'] = context
    pw_state['page'] = page

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

worker_thread = threading.Thread(target=playwright_worker, daemon=True)
worker_thread.start()

def execute(func):
    error_state['error'] = None
    task_queue.put(func)
    task_queue.join()
    if error_state['error']:
        raise error_state['error']
