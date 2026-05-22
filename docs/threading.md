# threading
https://docs.python.org/3/library/threading.html


## Where is `threading` used?
`pytest-testbook` plugin uses a separate thread for launching `playwright`. 

https://github.com/ldiary/pytest-testbook/blob/faf99551d7d741cb5424cfe8bc084aa7ba25555e/pytest_testbook/__init__.py#L53-L58

## Why use `threading`?
When `testbook` (which runs your notebook as a test) and the Jupyter kernel environment have already initialized an `asyncio` event loop, even with `nest_asyncio`, Playwright's `sync_api` detects that a loop is "running" and refuses to start, fearing thread-safety issues. 

To fix this, we need to **decouple** Playwright from the existing event loop by creating a fresh, non-running loop environment specifically for the browser initialization.

The Jupyter Notebook kernel on Windows creates an `asyncio` event loop the moment it starts. Playwright (both sync and async) detects this loop and, because of Windows-specific subprocess restrictions, refuses to run inside that specific loop to prevent a deadlock.

```
Error: It looks like you are using Playwright Sync API inside the asyncio loop.
Please use the Async API instead. 
```


You cannot fix this by setting policies because the Jupyter kernel has already initialized the loop before your code cell ever runs. The only way to run Playwright inside a Jupyter cell on Windows without triggering this loop error is to execute the Playwright code in a completely separate process, not the kernel thread itself.

```python
import subprocess
import sys
import os

# 1. Define the Playwright code as a string (this runs outside the Jupyter kernel)
script_code = """
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://www.google.com')
    print(f'Successfully landed on: {page.title()}')
    browser.close()
"""

# 2. Write it to a temporary file
script_name = "playwright_worker.py"
with open(script_name, "w") as f:
    f.write(script_code)

# 3. Execute it as a fresh process (bypassing the Jupyter Event Loop)
print("Executing in separate process...")
result = subprocess.run([sys.executable, script_name], capture_output=True, text=True)

# 4. Print the output from the worker process
if result.stdout:
    print(result.stdout)
if result.stderr:
    print(f"Error: {result.stderr}")

# 5. Cleanup
if os.path.exists(script_name):
    os.remove(script_name)
```

## The Playwright Blockade:
The Microsoft team behind Playwright explicitly hardcoded a rule that says: _"If an asynchronous loop is currently running, block the Synchronous API from starting."_ They did this to prevent Jupyter from freezing permanently.

## The Challenge
Find a way to run your exact synchronous code directly inside the cell without external scripts, string variables, or subprocess hacks.


## The "Clean Thread" Solution
Jupyter runs its protective "event loop" on the main thread. If we put the test code which launches playwright into a new thread, Playwright looks around, says "Hey, there's no event loop running here!", and executes perfectly. It completely bypasses both the Windows `NotImplementedError` and the Jupyter `asyncio` error. No weird string variables or `subprocess.run()`. It's just normal Python code recognized by Jupyter.

## The Architectural Truth: Why Playwright Blocks Your Code
You want to run this exact, synchronous code inside a Jupyter Notebook cell:
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    # ...
```

Here is the exact reason it fails: **Microsoft explicitly wrote Playwright to crash if you do this**. When you open a Jupyter Notebook, the Jupyter kernel immediately starts a background `asyncio` event loop to manage the notebook's interface and cell executions.

When you call `sync_playwright()`, Playwright looks at the Python thread and says: _"Is there an asyncio loop running here?"_ If the answer is yes, Playwright throws the `Error: It looks like you are using Playwright Sync API inside the asyncio loop` and deliberately crashes. They built this "safety switch" into the library to prevent the browser automation from permanently freezing the Jupyter interface.

Because that event loop is the lifeblood of the Jupyter kernel, you cannot turn it off. Therefore, **_Playwright officially does not support the Sync API inside Jupyter_**.

Since we cannot turn off Jupyter's event loop, and we cannot bypass Playwright's hardcoded safety switch, we have to outsmart them by giving Playwright an environment where it thinks there is no loop running.

We do this using Python's native `threading`. By pushing your exact code into a new, temporary thread, Playwright wakes up, looks around, sees an empty thread with no Jupyter event loop, and executes your synchronous code perfectly.

You do not need string variables, external files, or subprocesses. It executes natively right inside your cell. You avoid the Windows Subprocess Error: `NotImplementedError` entirely because the Sync API uses standard OS process creation, completely side-stepping Windows' broken asyncio implementation.

## The persistent: `NotImplementedError`
Because we spawned a brand-new thread, Windows gave that new thread its default event loop. On Windows, the default loop (`SelectorEventLoop`) does not support subprocesses. Playwright tried to spawn the Chromium browser process, hit the Windows restriction, and threw the `NotImplementedError`. We need to tell that specific new thread to use the Windows loop policy that allows subprocesses (`ProactorEventLoop`).

```python
import threading
import sys
import asyncio

# 1. The Thread Wrapper that fixes the Windows Subprocess issue
def run_safely_in_jupyter(func):
    def wrapper():
        # CRITICAL FIX: Tell this specific new thread to use the Proactor loop
        # so Windows allows Playwright to launch the Chromium subprocess.
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # Now run your Playwright code
        func()

    # Launch the thread
    thread = threading.Thread(target=wrapper)
    thread.start()
    thread.join() # Wait for the browser to finish before moving on

# 2. Your exact synchronous code
@run_safely_in_jupyter
def run_my_test():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://www.google.com')
        print(f"SUCCESS! Environment working. Landed on: {page.title()}")
        browser.close()
```

- [ ] **The Thread** hides Playwright from Jupyter so it doesn't crash on startup.
- [ ] **The Policy** (`WindowsProactorEventLoopPolicy`) ensures that when Playwright wakes up inside that thread, it has the correct Windows permissions to launch the `chromium.exe` subprocess.
