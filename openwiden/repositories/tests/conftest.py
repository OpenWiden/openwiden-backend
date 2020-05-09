import pytest

from . import factories
from openwiden.repositories import models


@pytest.fixture
def repository() -> models.Repository:
    return factories.Repository()


@pytest.fixture
def create_repository():
    def factory(**kwargs) -> models.Repository:
        return factories.Repository(**kwargs)

    return factory


@pytest.fixture
def issue() -> models.Issue:
    return factories.Issue()


@pytest.fixture
def create_issue():
    def factory(**kwargs) -> models.Issue:
        return factories.Issue(**kwargs)

    return factory
