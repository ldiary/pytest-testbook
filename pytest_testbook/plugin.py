# -*- coding: utf-8 -*-
import os
import sys
import pytest
import nbformat
import re
import pprint
from pathlib import Path
from queue import Empty
from jupyter_client import KernelManager

# Modern global state management (replacing sys.modules hack)
_km = None
_kc = None
_setup_done = False


def pytest_addhooks(pluginmanager):
    """Register plugin hooks."""
    try:
        from pytest_testbook import hooks
        pluginmanager.add_hookspecs(hooks)
    except ImportError:
        pass  # Handle gracefully if the hooks module is unavailable


def pytest_collect_file(file_path, parent):
    """Modern pytest hook using pathlib.Path (file_path)."""
    if file_path.suffix == ".ipynb":
        # Use from_parent instead of direct instantiation
        return Testbook.from_parent(parent, path=file_path)


def pytest_sessionstart(session):
    """ before session.main() is called. """
    global _km, _kc
    _km = KernelManager()
    _km.start_kernel()
    _kc = _km.client()
    _kc.start_channels()
    _kc.wait_for_ready()


def pytest_sessionfinish(session, exitstatus):
    """ whole test run finishes. """
    global _km, _kc
    if _kc:
        # Quits the browser if it still exists
        _kc.execute("try:\n    browser.quit()\nexcept:\n    pass\n", allow_stdin=False)
        _kc.stop_channels()
    if _km:
        _km.shutdown_kernel(now=True)


class Testbook(pytest.File):
    def collect(self):
        # Modern pytest uses self.path (pathlib.Path)
        nb = nbformat.read(self.path.open(encoding="utf-8"), 4)

        self.km = _km
        self.kc = _kc
        self.case = ""
        setup = False
        self.test_setup = []

        name = "Default_Name"

        for cell in nb.cells:
            if cell.cell_type == 'markdown':
                if "## Test Results" in cell.source:
                    return
                if '## Test Configurations' in cell.source or '## Environmental Needs' in cell.source:
                    setup = True
                    continue
                if cell.source.startswith("## TC"):
                    case, _, _ = cell.source.partition("](https")
                    self.case = case.replace("## ", "").replace("[", "")

                for step in ["### Given", "### And", "### When", "### Then", "### But"]:
                    if cell.source.startswith(step):
                        setup = False
                        self.header = cell.source.split("\n")[0].replace("### ", "")
                        header_clean = re.sub(r'### |\(|\)|\"|\'', '', self.header)
                        # Modern path name resolution
                        self.header = f"{self.path.stem}.{self.header}"
                        name = header_clean.strip().replace(" ", "_").lower()

            elif cell.cell_type == 'code' and nb.metadata.get('kernelspec', {}).get('language') == 'python':
                if setup:
                    self.test_setup.append(cell.source)
                    continue
                if name == "Default_Name":
                    continue

                # Modern node yielding via from_parent
                yield Teststep.from_parent(
                    self,
                    name=name,
                    case=self.case,
                    header=self.header,
                    cell=cell
                )

    def setup(self):
        # Safely trigger hooks if they exist
        if hasattr(self.config.hook, 'pytest_testbook_kernel_setup'):
            self.config.hook.pytest_testbook_kernel_setup(scenario=self)

        global _setup_done
        if not _setup_done:
            for setup_code in self.test_setup:
                send_and_execute(self, setup_code)
            _setup_done = True

    def teardown(self):
        if hasattr(self.config.hook, 'pytest_testbook_kernel_teardown'):
            self.config.hook.pytest_testbook_kernel_teardown(scenario=self)


class TestbookException(Exception):
    """ custom exception for error reporting. """


def send_and_execute(item, source, allow_stdin=False):
    if isinstance(item, Testbook):
        kernel = item.kc
    elif isinstance(item, Teststep):
        kernel = item.parent.kc
    else:
        raise TestbookException("Unknown Item")

    run_id = kernel.execute(source, allow_stdin=allow_stdin)
    timeout = 1800  # 1800 seconds == 30 minutes

    while True:
        try:
            reply = kernel.get_shell_msg(timeout=timeout)
            if reply.get("parent_header", {}) and reply["parent_header"].get("msg_id") == run_id:
                break
        except Empty:
            # Fixed old string formatting bug here
            raise TestbookException(f"Timeout of {timeout} seconds exceeded executing cell: {source}")

    status = reply['content'].get('status')

    if status == 'ok':
        return "Test successfully completed."

    elif status == 'error':
        _traceback = reply['content'].get('traceback', [])
        colored_traceback = "\n".join(_traceback)
        uncolored_traceback = re.sub(r'\x1b[^m]*m', '', "\n".join(_traceback))

        if isinstance(item, Teststep):
            item._location = (item.location[0], item.location[1], item.header)
            if item.config.getvalue("color") == 'yes':
                item.traceback = colored_traceback
            else:
                item.traceback = uncolored_traceback
        elif isinstance(item, Testbook):
            if item.config.getvalue("color") == 'yes':
                print(colored_traceback)
            else:
                print(uncolored_traceback)
        raise TestbookException(source, _traceback)

    elif status == 'aborted':
        raise TestbookException(source, "Test was aborted")
    else:
        pprint.pprint(reply)
        pprint.pprint(reply['content'])
        raise TestbookException(source, "Unknown Status Code")


class Teststep(pytest.Item):

    @classmethod
    def from_parent(cls, parent, *, name, case, header, cell):
        # Modern initialization overriding from_parent
        obj = super().from_parent(parent, name=name)
        obj.case = case
        obj.header = header
        obj.cell = cell
        return obj

    def runtest(self):
        send_and_execute(self, self.cell.source)

    def repr_failure(self, excinfo):
        if isinstance(excinfo.value, TestbookException):
            # Modern Python attribute checking
            tb = getattr(self, 'traceback', "\n".join(str(a) for a in excinfo.value.args))
            return f"{self.cell.source}\n\n{tb}"
        return super().repr_failure(excinfo)


def pytest_addoption(parser):
    group = parser.getgroup('testbook')
    group.addoption(
        '--kernel_reuse',
        action='store',
        dest='dest_foo',  # Note: ensure this destination variable is intentional
        default='no',
        help='Do you want to allow multiple testbooks to be run on the same kernel?'
    )