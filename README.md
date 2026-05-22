pytest-testbook
===================================

[![Build Status](https://github.com/ldiary/pytest-testbook/actions/workflows/tests.yml/badge.svg)](https://github.com/ldiary/pytest-testbook/actions/workflows/tests.yml) 
[![See Build Status on AppVeyor](https://ci.appveyor.com/api/projects/status/github/ldiary/pytest-testbook?branch=master)](https://ci.appveyor.com/project/ldiary/pytest-testbook/branch/master)

Question
-----
What do you call a Jupyter Notebook filled with test cases?

Answer
-----
a `testbook` !


Why invent this plugin?
----
Because it allows specification, test cases, and automation code to be recorded inside a single Jupyter Notebook. When specification, requirements, test cases, and automation code are written in one place, this place is called a `testbook`. 

How to run the tests?
----
- Option 1: Follow the manual steps written in the `testbook` and perform each test steps manually.
- Option 2: Trigger the execution of automated test code by running the each cell directly in Jupyter.
- Option 3: Use `pytest` to discover tests inside the `testbook` and run them. This option enables your tests to run in CI/CD pipeline. 


Features
--------

* BDD-style specification, requirements, manual test steps, and test automation code.
* Auto-generated PDF reports to support auditing processes.
* Plugin managed `playwright` instance inside Jupyter Notebook.
* Trigger automated tests execution in Jupyter.
* Upload `testbook` in CI/CD pipepline for auto-execution using `pytest`


Installation
------------
You will need to install playwright to generate pdf test reports. The side-effect is that you get a free playwright instance that you can use in your Testbooks.

```
pip install pytest-testbook
pip install jupyterlab
playwright install chromium
```

Usage
-----
Navigate to where your tests folder are located. Then either run:
```
jupyter lab
```
to run tests manually in Jupyter. Or you can run:

```
pytest -sv
```
instead to let `pytest` discover your tests, collect them and execute them.


Contributing
------------
Contributions are very welcome. Tests can be run with `tox`_, please ensure
the coverage at least stays the same before you submit a pull request.

License
-------

Distributed under the terms of the `MIT`_ license, "pytest-testbook" is free and open source software

