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
Because no one can stop you from jotting your test cases inside Jupyter Notebook. In the same way that no one can stop your BA from writing their requirements inside that same Notebook. Moreover, no one can stop the test automation engineer from writing test automation code in that same Notebook. When requirements, test cases, and automation code are written in one single Notebook, this becomes a Testbook.


Features
--------

* PDF reports for auditing purposes.
* `pytest-testbook` managed `playwright` instance.
* BDD-style tests.
* Run tests manually in Jupyter or automated using `pytest`


Installation
------------
You will need playwright to generate pdf test reports. The side-effect is that you get a free playwright instance that you can use in your Testbooks.

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

