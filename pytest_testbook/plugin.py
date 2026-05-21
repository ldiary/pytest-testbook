# -*- coding: utf-8 -*-
import sys
import pytest
import nbformat
import re
import io
import shutil
import textwrap
import datetime
import subprocess
import re
from queue import Empty
from jupyter_client import KernelManager

# Modern global state management
_km = None
_kc = None
_session = None
_setup_done = False
_session_start_time = None

# ANSI escape sequence regex
ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


def get_git_info():
    """Returns (branch_name, commit_hash) or (None, None) if not a git repo."""
    try:
        # Get branch name
        branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            stderr=subprocess.DEVNULL, text=True
        ).strip()

        # Get full commit hash
        commit = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'],
            stderr=subprocess.DEVNULL, text=True
        ).strip()

        return branch, commit
    except Exception:
        return "N/A", "N/A"



def pytest_addhooks(pluginmanager):
    try:
        from pytest_testbook import hooks
        pluginmanager.add_hookspecs(hooks)
    except ImportError:
        pass


def pytest_collect_file(file_path, parent):
    """Modern pytest hook using pathlib.Path (file_path)."""
    if file_path.suffix == ".ipynb":
        # Ignore generated report files to prevent infinite test loops
        if file_path.name.endswith("_report_.ipynb"):
            return None

        # Use from_parent instead of direct instantiation
        return Testbook.from_parent(parent, path=file_path)


def pytest_sessionstart(session):
    global _km, _kc, _session_start_time, _session
    _session = session  # Store the session object
    _session_start_time = datetime.datetime.now()
    _km = KernelManager()
    _km.start_kernel()
    _kc = _km.client()
    _kc.start_channels()
    _kc.wait_for_ready()


def pytest_sessionfinish(session, exitstatus):
    global _km, _kc
    if _kc:
        try:
            _kc.execute("try:\n    browser.quit()\nexcept:\n    pass\n", allow_stdin=False)
        except Exception:
            pass
        try:
            _kc.stop_channels()
        except Exception:
            pass
    if _km:
        try:
            _km.shutdown_kernel(now=True)
        except Exception:
            pass


class Testbook(pytest.File):
    def collect(self):
        # 1. Initialize the storage list for our Teststeps
        self._teststeps = []

        nb = nbformat.read(self.path.open(encoding="utf-8"), 4)
        self.km = _km
        self.kc = _kc
        self.case = ""
        setup = False
        self.test_setup = []
        name = "Default_Name"

        for cell in nb.cells:
            # ... (your existing markdown parsing logic) ...
            if cell.cell_type == 'markdown':
                if "## Test Results" in cell.source: continue
                if '## Test Configurations' in cell.source or '## Environmental Needs' in cell.source:
                    setup = True;
                    continue
                if cell.source.startswith("## TC"):
                    case, _, _ = cell.source.partition("](https")
                    self.case = case.replace("## ", "").replace("[", "")
                for step in ["### Given", "### And", "### When", "### Then", "### But"]:
                    if cell.source.startswith(step):
                        setup = False
                        self.header = cell.source.split("\n")[0].replace("### ", "")
                        header_clean = re.sub(r'### |\(|\)|\"|\'', '', self.header)
                        self.header = f"{self.path.stem}.{self.header}"
                        name = header_clean.strip().replace(" ", "_").lower()

            elif cell.cell_type == 'code' and nb.metadata.get('kernelspec', {}).get('language') == 'python':
                if setup:
                    self.test_setup.append(cell.source)
                    continue
                if name == "Default_Name": continue

                # 2. Yield the item AND append it to our tracking list
                item = Teststep.from_parent(self, name=name, case=self.case, header=self.header, cell=cell)
                self._teststeps.append(item)
                yield item

    def teardown(self):
        # 1. Gather results
        passed_count = 0
        failed_count = 0
        report_lines = []

        for child in self._teststeps:
            status = child.outcome
            if status == "PASSED":
                passed_count += 1
                status_emoji = "✅"
                status_display = "**PASSED**"
            else:
                failed_count += 1
                status_emoji = "❌"
                status_display = "**FAILED**"

            report_lines.append(f"{status_emoji} {child.nodeid} {status_display}")

            if child.output.strip():
                # 1. Clean the output
                clean_output = child.output.strip().replace('\\n', '\n')

                # 2. DECISION: If it looks like a traceback (contains "Traceback"),
                # don't wrap it. Just print it as-is.
                if "Traceback" in clean_output:
                    report_lines.append(f"  {clean_output}")
                else:
                    # Otherwise, use textwrap for normal print statements
                    wrapped_text = textwrap.fill(
                        clean_output,
                        width=100,
                        subsequent_indent="    "
                    )
                    report_lines.append(f"  {wrapped_text}")

            branch, commit = get_git_info()
            git_str = f"git commit: {commit}\ngit branch: {branch}"
            # 2. Get Plugin Info and Collected Count
            plugin_list = []
            # Access pluginmanager from the stored session config
            for plugin, dist in _session.config.pluginmanager.list_plugin_distinfo():
                plugin_list.append(f"{dist.project_name}-{dist.version}")

            plugins_str = "plugins: " + ", ".join(plugin_list)
            collected_str = f"collected {len(_session.items)} items"

            # 3. Calculate duration
            end_time = datetime.datetime.now()
            duration = (end_time - _session_start_time).total_seconds()

            # 4. Build the Summary Footer
            summary = []
            if passed_count > 0: summary.append(f"{passed_count} passed")
            if failed_count > 0: summary.append(f"{failed_count} failed")

            footer_text = ", ".join(summary)
            summary_line = f"{footer_text} in {duration:.2f}s"

            # 5. Construct Final Report
            # Include the plugins and collected info in the header/top section
            header = "=" * 100 + " test session starts " + "=" * 100
            # Add git_str to meta_info
            meta_info = f"{plugins_str}\n{git_str}\n{collected_str}"
            footer_line = "=" * 100 + f" {summary_line} " + "=" * 100

            full_report = f"{header}\n{meta_info}\n\n" + "\n".join(report_lines) + f"\n\n{footer_line}"

        # 6. Save to the notebook
        if full_report:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            date, _ = timestamp.split("_")
            new_filename = f"{self.path.stem}_{timestamp}_report_.ipynb"
            new_path = self.path.parent / "reports" / date / new_filename

            # --- ADDED: Create the directory structure automatically ---
            new_path.parent.mkdir(parents=True, exist_ok=True)
            # ---------------------------------------------------------

            shutil.copy(self.path, new_path)
            nb = nbformat.read(new_path.open(encoding="utf-8"), 4)
            log_content = f"## Test Results\n**Executed at:** {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n```text\n{full_report}\n```"
            nb.cells.append(nbformat.v4.new_markdown_cell(log_content))

            # ... (keep your notebook writing logic) ...
            with new_path.open('w', encoding="utf-8") as f:
                nbformat.write(nb, f)

            # --- UPDATED: PDF Generation Toggle ---
            # Check the configuration option passed from conftest.py
            if self.config.getoption("--generate-pdf"):
                print(f"\n  Generating PDF for {new_path.name}...")

                import time
                time.sleep(0.5)

                if new_path.stat().st_size > 0:
                    try:
                        # Call the conversion (include --no-input if you want the "Summary" version)
                        subprocess.run(
                            [
                                "jupyter", "nbconvert",
                                "--to", "webpdf",
                                "--allow-chromium-download",
                                str(new_path)
                            ],
                            capture_output=True,
                            text=True
                        )
                        print(f"  Successfully generated PDF: {new_path.with_suffix('.pdf')}")
                    except Exception as e:
                        print(f"  PDF Conversion failed: {e}")
                else:
                    print("  Skipping PDF: File is empty.")
            else:
                print("  PDF generation disabled via configuration.")
            # --------------------------------------

class TestbookException(Exception):
    pass


def send_and_execute(item, source):
    kernel = item.parent.kc
    run_id = kernel.execute(source, allow_stdin=False)
    output_buffer = io.StringIO()

    # Listen to IOPub
    while True:
        try:
            msg = kernel.get_iopub_msg(timeout=1800)
            if msg.get("parent_header", {}).get("msg_id") == run_id:
                msg_type = msg.get("header", {}).get("msg_type")
                content = msg.get("content", {})
                if msg_type == "stream":
                    text = content.get("text", "")
                    sys.stdout.write(text)
                    output_buffer.write(text)
                elif msg_type in ("execute_result", "display_data"):
                    text = content.get("data", {}).get("text/plain", "")
                    if text:
                        output_buffer.write(text + "\n")
                elif msg_type == "status" and content.get("execution_state") == "idle":
                    break
        except Empty:
            raise TestbookException("Timeout")

    # Check Status
    reply = kernel.get_shell_msg(timeout=5)
    if reply['content']['status'] == 'error':
        # --- CLEAN TRACEBACK LOGIC ---
        raw_traceback = reply['content'].get('traceback', [])
        # Strip ANSI codes and convert list to a single clean string
        clean_traceback = [ANSI_ESCAPE.sub('', line) for line in raw_traceback]
        readable_traceback = "\n".join(clean_traceback)

        # Raise the exception with the clean traceback
        raise TestbookException(source, readable_traceback)

    return output_buffer.getvalue()


class Teststep(pytest.Item):
    @classmethod
    def from_parent(cls, parent, *, name, case, header, cell):
        obj = super().from_parent(parent, name=name)
        obj.case = case
        obj.header = header
        obj.cell = cell
        obj.output = ""
        obj.outcome = "PASSED"

        # Add a flag to the parent (the Testbook) to track setup status
        if not hasattr(parent, '_setup_run'):
            parent._setup_run = False
        return obj

    def runtest(self):
        # 1. Arrange: Run setup if not done
        if not self.parent._setup_run:
            for setup_source in self.parent.test_setup:
                send_and_execute(self, setup_source)
            self.parent._setup_run = True

        # 2. Execute the notebook cell directly
        try:
            self.output = send_and_execute(self, self.cell.source)
            self.outcome = "PASSED"
        except Exception as e:
            self.outcome = "FAILED"
            self.output += f"\n\n--- ERROR ---\n{str(e)}"
            raise

    def repr_failure(self, excinfo):
        return f"{self.cell.source}\n\n{excinfo.value}"