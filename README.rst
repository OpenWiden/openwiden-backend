OpenWiden
=========

OpenWiden - An Open Source Project Search Platform.

.. image:: https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg
     :target: https://github.com/pydanny/cookiecutter-django/
     :alt: Built with Cookiecutter Django
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
     :target: https://github.com/ambv/black
     :alt: Black code style
.. image:: https://github.com/OpenWiden/openwiden-backend/workflows/Tests/badge.svg
     :alt: Tests
.. image:: https://codecov.io/gh/OpenWiden/openwiden-backend/branch/master/graph/badge.svg
     :target: https://codecov.io/gh/OpenWiden/openwiden-backend
     :alt: Codecov


:License: GPLv3

Local Development
-----------------

Start server::

    $docker-compose -f local.yml up

Or using a shortcut via [make]::

    $ make up

Run a command inside the docker container::

    $ docker-compose run --rm web [command]

Or using a shortcut via [make]::

    $  make web c="python --version"
