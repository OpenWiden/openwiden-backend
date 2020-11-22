OpenWiden
=========

OpenWiden - An Open Source Project Search Platform.

.. image:: https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg
    :target: https://github.com/pydanny/cookiecutter-django/
    :alt: Built with Cookiecutter Django

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/ambv/black
    :alt: Black code style

.. image:: https://github.com/OpenWiden/openwiden-backend/workflows/CI/badge.svg
    :target: https://github.com/OpenWiden/openwiden-backend/actions
    :alt: Tests

.. image:: https://codecov.io/gh/OpenWiden/openwiden-backend/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/OpenWiden/openwiden-backend
    :alt: Codecov

.. image:: https://pyup.io/repos/github/OpenWiden/openwiden-backend/shield.svg?t=1600509476425
    :target: https://pyup.io/repos/github/OpenWiden/openwiden-backend/
    :alt: PyUp

:License: GPLv3

Local Development
-----------------

Start server::

    $ docker-compose -f local.yml up

Or using a shortcut via [make]::

    $ make up

Run a command inside the docker container::

    $ docker-compose run --rm web [command]

Or using a shortcut via [make]::

    $  make web c="python --version"
