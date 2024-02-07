.. _installation:

Installation
============

Clone the repository with:

.. code-block:: bash

  git clone https://github.com/twpalab/qutegds

then to install it in normal mode:

.. code-block:: bash

  pip install .

Use poetry to install the latest version in developer mode, remember to also
install the pre-commits!

.. code-block:: bash

  poetry install --with docs,analysis
  pip install pre-commit
  pre-commit install


The optional packages are

- ``analysis`` for code testing.
- ``docs`` for the documentation source and compilation.
