### Setup virtual environment
```
C:\Users\ernesto.luzon>python "C:\Program Files\Python35\Tools\scripts\pyvenv.py" testbookenv
C:\Users\ernesto.luzon>testbookenv\Scripts\activate.bat
```
### Install pytest-testbook
```
(testbookenv) C:\Users\ernesto.luzon>pip install pytest-testbook
(testbookenv) C:\Users\ernesto.luzon>pip freeze
colorama==0.3.7
decorator==4.0.10
entrypoints==0.2.2
ipykernel==4.3.1
ipython==4.2.1
ipython-genutils==0.1.0
ipywidgets==5.1.5
Jinja2==2.8
jsonschema==2.5.1
jupyter==1.0.0
jupyter-client==4.3.0
jupyter-console==5.0.0
jupyter-core==4.1.0
MarkupSafe==0.23
mistune==0.7.3
nbconvert==4.2.0
nbformat==4.0.1
notebook==4.2.1
pickleshare==0.7.2
prompt-toolkit==1.0.3
py==1.4.31
Pygments==2.1.3
pytest==2.9.2
pytest-testbook==0.0.5
pyzmq==15.3.0
qtconsole==4.2.1
simplegeneric==0.8.1
six==1.10.0
tornado==4.3
traitlets==4.2.2
wcwidth==0.1.7
widgetsnbextension==1.2.3
```

### Run the tests in Pytest 2.9.2
```
(testbookenv) C:\Users\ernesto.luzon>cd pytest-testbook\tests\testbooks

(testbookenv) C:\Users\ernesto.luzon\pytest-testbook\tests\testbooks>python
Python 3.5.1 (v3.5.1:37a07cee5969, Dec  6 2015, 01:54:25) [MSC v.1900 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license" for more information.
>>> import os
>>> import pytest
>>> os.getcwd()
'C:\\Users\\ernesto.luzon\\pytest-testbook\\tests\\testbooks'
>>> os.chdir(os.path.join(os.getcwd(), "colo", "Service_and_Order"))
>>> os.getcwd()
'C:\\Users\\ernesto.luzon\\pytest-testbook\\tests\\testbooks\\colo\\Service_and_Order'
>>> arguments = '-sv --collect-only --junitxml=616_testlog.xml "Provision Colo Service.ipynb"'
>>> pytest.main(args=arguments)
============================= test session starts =============================
platform win32 -- Python 3.5.1, pytest-2.9.2, py-1.4.31, pluggy-0.3.1 -- C:\Users\ernesto.luzon\testbookenv\Scripts\python.exe
cachedir: ..\..\..\..\.cache
rootdir: C:\Users\ernesto.luzon\pytest-testbook, inifile:
plugins: testbook-0.0.5

 generated xml file: C:\Users\ernesto.luzon\pytest-testbook\tests\testbooks\colo\Service_and_Order\616_testlog.xml
======================== no tests ran in 0.81 seconds =========================
ERROR: file not found: "Provision Colo Service.ipynb"
4
>>> exit()
```

### Run the tests in Pytest 2.9.1
```
(testbookenv) C:\Users\ernesto.luzon\pytest-testbook\tests\testbooks>pip install pytest==2.9.1
Collecting pytest==2.9.1
  Using cached pytest-2.9.1-py2.py3-none-any.whl
Requirement already satisfied (use --upgrade to upgrade): py>=1.4.29 in c:\users\ernesto.luzon\testbookenv\lib\site-packages (from pytest==2.9.1)
Requirement already satisfied (use --upgrade to upgrade): colorama; sys_platform == "win32" in c:\users\ernesto.luzon\testbookenv\lib\site-packages (from pytest==2.9.1)
Installing collected packages: pytest
  Found existing installation: pytest 2.9.2
    Uninstalling pytest-2.9.2:
      Successfully uninstalled pytest-2.9.2
Successfully installed pytest-2.9.1

(testbookenv) C:\Users\ernesto.luzon\pytest-testbook\tests\testbooks>python
Python 3.5.1 (v3.5.1:37a07cee5969, Dec  6 2015, 01:54:25) [MSC v.1900 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license" for more information.
>>> import os
>>> import pytest
>>> os.getcwd()
'C:\\Users\\ernesto.luzon\\pytest-testbook\\tests\\testbooks'
>>> os.chdir(os.path.join(os.getcwd(), "colo", "Service_and_Order"))
>>> os.getcwd()
'C:\\Users\\ernesto.luzon\\pytest-testbook\\tests\\testbooks\\colo\\Service_and_Order'
>>> arguments = '-sv --collect-only --junitxml=616_testlog.xml "Provision Colo Service.ipynb"'
>>> pytest.main(args=arguments)
============================= test session starts =============================
platform win32 -- Python 3.5.1, pytest-2.9.1, py-1.4.31, pluggy-0.3.1 -- C:\Users\ernesto.luzon\testbookenv\Scripts\python.exe
cachedir: ..\..\..\..\.cache
rootdir: C:\Users\ernesto.luzon\pytest-testbook, inifile:
plugins: testbook-0.0.5
collected 9 items
<Testbook 'Provision Colo Service'>
  <Teststep 'when_i_prepare_customer'>
  <Teststep 'when_i_prepare_contact'>
  <Teststep 'when_i_create_and_edit_room'>
  <Teststep 'when_i_create_and_edit_rack'>
  <Teststep 'when_i_create_and_edit_cage'>
  <Teststep 'when_i_create_and_edit_sensor'>
  <Teststep 'when_i_create_and_edit_gate'>
  <Teststep 'when_i_prepare_account_manager'>
  <Teststep 'when_i_activate_colo_cab'>

 generated xml file: C:\Users\ernesto.luzon\pytest-testbook\tests\testbooks\colo\Service_and_Order\616_testlog.xml
======================== no tests ran in 0.18 seconds =========================
0
>>> exit()
```




