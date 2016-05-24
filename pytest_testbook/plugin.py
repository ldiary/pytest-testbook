# -*- coding: utf-8 -*-
import os
import sys
import pytest
import nbformat
import ntpath
import re
import pprint
from queue import Empty
from jupyter_client import KernelManager

testbook = sys.modules[__name__]
setup_done = None

def pytest_addhooks(pluginmanager):
    """Register plugin hooks."""
    from pytest_testbook import hooks
    pluginmanager.add_hookspecs(hooks)


def pytest_collect_file(parent, path):
    if path.ext == ".ipynb":
        return Testbook(path, parent)

def pytest_sessionstart(session):
    """ before session.main() is called. """
    testbook.km = KernelManager()
    testbook.km.start_kernel()
    testbook.kc = testbook.km.client()
    testbook.kc.start_channels()
    testbook.kc.wait_for_ready()


def pytest_sessionfinish(session, exitstatus):
    """ whole test run finishes. """

    # TODO: Move this code into a hookspec
    # Quits the browser if it still exists
    testbook.kc.execute("browser.quit()\n", allow_stdin=False)
    testbook.kc.stop_channels()
    testbook.km.shutdown_kernel(now=True)


class Testbook(pytest.File):

    def collect(self):
        nb = nbformat.read(self.fspath.open(), 4)
        self.km = testbook.km
        self.kc = testbook.kc

        self.name = ntpath.basename(self.name).replace(".ipynb", "")

        name = "Default Name"
        self.case = ""
        setup = False
        self.test_setup = []
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
                        header = re.sub(r'### |\(|\)|\"|\'', '', self.header)
                        self.header = ".".join([self.name, self.header])
                        name = header.strip().replace(" ", "_").lower()
            if cell.cell_type == 'code' and nb.metadata.kernelspec.language == 'python':
                if setup:
                    self.test_setup.append(cell.source)
                    continue
                if name == "Default Name":
                    continue
                yield Teststep(self.case, self.header, name, self, cell)

    def setup(self):
        # self.km.restart_kernel()
        self.config.hook.pytest_testbook_kernel_setup(scenario=self)
        # TODO: Move this code into an OPTION
        if not testbook.setup_done:
            for setup in self.test_setup:
                send_and_execute(self, setup)
            testbook.setup_done = True

    def teardown(self):
        self.config.hook.pytest_testbook_kernel_teardown(scenario=self)
        # self.kc.stop_channels()
        # self.km.shutdown_kernel(now=True)


class TestbookException(Exception):
    """ custom exception for error reporting. """


def send_and_execute(item, source, allow_stdin=False):
    if isinstance(item, Testbook):
        kernel = item.kc
    elif isinstance(item, Teststep):
        kernel = item.parent.kc
    else:
        raise(TestbookException("Unknown Item"))

    # Reuse browser
    if "browser.quit()" in source:
        source = source.replace("test.browser.quit()", '')
        source = source.replace("browser.quit()", '')
    run_id = kernel.execute(source, allow_stdin=allow_stdin)
    timeout = 1800  # 1800seconds == 30minutes
    while True:
        try:
            reply = kernel.get_shell_msg(block=True, timeout=timeout)
            if reply.get("parent_header", None) and reply["parent_header"].get("msg_id", None) == run_id:
                break
        except Empty:
            raise TestbookException("Timeout of %d seconds exceeded executing cell: %s"(timeout, source))

    if reply['content']['status'] == 'ok':
        return "Test successfully completed."

    elif reply['content']['status'] == 'error':
        _traceback = reply['content']['traceback']
        colored_traceback = "\n".join(_traceback)
        uncolored_traceback = re.sub(r'\x1b[^m]*m', '', "\n".join(_traceback))
        if isinstance(item, Teststep):
            item._location = (item._location[0], item._location[1], item.header)
            if item.config.getvalue("color") == 'yes':
                setattr(item, 'traceback', colored_traceback)
            else:
                setattr(item, 'traceback', uncolored_traceback)
        elif isinstance(item, Testbook):
            if item.config.getvalue("color") == 'yes':
                print(colored_traceback)
            else:
                print(uncolored_traceback)
        raise TestbookException(source, _traceback)

    elif reply['content']['status'] == 'aborted':
        raise TestbookException(source, "Test was aborted")
    else:
        pprint.pprint(reply)
        pprint.pprint(reply['content'])
        raise TestbookException(source, "Unknown Status Code")


class Teststep(pytest.Item):

    def __init__(self, case, header, name, parent, cell):
        super(Teststep, self).__init__(name, parent)
        self.case = case
        self.header = header
        self.cell = cell

    def runtest(self):
        send_and_execute(self, self.cell.source)

    def repr_failure(self, excinfo):
        if isinstance(excinfo.value, TestbookException):
            try:
                return ("\n\n".join([self.cell.source, self.traceback]))
            except AttributeError:
                return ("\n\n".join([self.cell.source, "\n".join(excinfo.value.args)]))
        else:
            return super(Teststep, self).repr_failure(excinfo)


def pytest_addoption(parser):
    group = parser.getgroup('testbook')
    group.addoption(
        '--kernel_reuse',
        action='store',
        dest='dest_foo',
        default='no',
        help='Do you want to allow multiple testbooks to be run on the same kernel?'
    )

    # parser.addini('HELLO', 'Dummy pytest.ini setting')

