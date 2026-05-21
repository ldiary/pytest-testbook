import nbformat as nbf
import os

nb = nbf.v4.new_notebook()

# Define the cells using BDD Given/When/Then Syntax
cells = [
    nbf.v4.new_markdown_cell("## An example of using Jupyter for Documenting and Automating BDD Style Tests"),

    nbf.v4.new_markdown_cell("### Given the Playwright background worker is running"),
    nbf.v4.new_code_cell(
        """import threading\nimport sys\nimport asyncio\nimport queue\nfrom playwright.sync_api import sync_playwright\n\ntask_queue = queue.Queue()\npw_state = {}\nerror_state = {'error': None}\n\ndef playwright_worker():\n    if sys.platform == 'win32':\n        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())\n    \n    pw = sync_playwright().start()\n    browser = pw.chromium.launch(headless=True)\n    page = browser.new_page()\n    \n    pw_state['pw'] = pw\n    pw_state['browser'] = browser\n    pw_state['page'] = page\n    \n    while True:\n        task = task_queue.get()\n        if task is None:\n            break\n        try:\n            task(pw_state)\n        except Exception as e:\n            error_state['error'] = e\n        task_queue.task_done()\n        \n    browser.close()\n    pw.stop()\n\nworker_thread = threading.Thread(target=playwright_worker, daemon=True)\nworker_thread.start()\n\ndef execute(func):\n    error_state['error'] = None\n    task_queue.put(func)\n    task_queue.join()\n    if error_state['error']:\n        raise error_state['error']"""),

    nbf.v4.new_markdown_cell("### When I navigate to Google"),
    nbf.v4.new_code_cell(
        """def go_to_google(state):\n    page = state['page']\n    page.goto('https://www.google.com')\n    try:\n        page.click('button:has-text(\"Accept all\")', timeout=2000)\n    except:\n        pass\n    \n    assert 'Google' in page.title(), f\"Expected 'Google', got {page.title()}\"\n    \nexecute(go_to_google)"""),

    nbf.v4.new_markdown_cell("### Then I can search for genuflect"),
    nbf.v4.new_code_cell(
        """def search_term(state):\n    page = state['page']\n    search_box = page.locator(\"textarea[name='q'], input[name='q']\").first\n    search_box.fill(\"genuflect\")\n    page.keyboard.press(\"Enter\")\n    \n    page.wait_for_load_state(\"networkidle\")\n    \n    assert 'genuflect' in page.title().lower(), \"Search did not complete successfully\"\n    \nexecute(search_term)"""),

    nbf.v4.new_markdown_cell("### And the browser shuts down cleanly"),
    nbf.v4.new_code_cell("""task_queue.put(None)\nworker_thread.join(timeout=10)""")
]

nb['cells'] = cells

# --- THE FIX: ADD THE METADATA YOUR PLUGIN EXPECTS ---
nb.metadata = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3"
    }
}
# -----------------------------------------------------

os.makedirs('', exist_ok=True)

file_path = 'test_persistent_playwright.ipynb'
with open(file_path, 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print("BDD Notebook generated successfully with required kernelspec.")