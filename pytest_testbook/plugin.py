# -*- coding: utf-8 -*-
import sys
import pytest
import nbformat
import re
import io
import shutil
import textwrap
import datetime
from queue import Empty
from jupyter_client import KernelManager

# Modern global state management
_km = None
_kc = None
_setup_done = False
_session_start_time = None



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
    global _km, _kc, _session_start_time
    _session_start_time = datetime.datetime.now() # Capture start time
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
                wrapped_text = textwrap.fill(
                    child.output.strip(),
                    width=100,
                    subsequent_indent="    "
                )
                report_lines.append(f"  {wrapped_text}")

        # 2. Calculate duration
        end_time = datetime.datetime.now()
        duration = (end_time - _session_start_time).total_seconds()

        # 3. Build the Summary Footer
        summary = []
        if passed_count > 0: summary.append(f"{passed_count} passed")
        if failed_count > 0: summary.append(f"{failed_count} failed")

        footer_text = ", ".join(summary)
        footer = f"{footer_text} in {duration:.2f}s"

        # 4. Construct Final Report
        header = "=" * 100 + " test session starts " + "=" * 100
        footer_line = "=" * 100 + f" {footer} " + "=" * 100

        full_report = f"{header}\n\n" + "\n".join(report_lines) + f"\n\n{footer_line}"

        # 5. Save to the notebook
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

            with new_path.open('w', encoding="utf-8") as f:
                nbformat.write(nb, f)

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
        raise TestbookException(source, reply['content'].get('traceback', []))

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
        try:
            # 1. Arrange: Run setup ONLY ONCE
            if not self.parent._setup_run:
                for setup_source in self.parent.test_setup:
                    send_and_execute(self, setup_source)
                self.parent._setup_run = True

            # 2. Act: Execute the actual test cell logic
            self.output = send_and_execute(self, self.cell.source)
            self.outcome = "PASSED"

        except Exception as e:
            self.outcome = "FAILED"
            self.output += f"\n\n--- ERROR ---\n{str(e)}"
            raise

    def repr_failure(self, excinfo):
        return f"{self.cell.source}\n\n{excinfo.value}"