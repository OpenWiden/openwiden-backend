import factory
from django.utils.timezone import get_current_timezone
from factory import fuzzy

from openwiden.repositories import models, enums as repo_enums
from openwiden.users.tests.factories import VCSAccountFactory
from openwiden.organizations.tests import factories as org_factories
from openwiden import enums

from faker import Faker

fake = Faker()


class Repository(factory.django.DjangoModelFactory):
    vcs = fuzzy.FuzzyChoice(enums.VersionControlService.choices, getter=lambda c: c[0])
    remote_id = fuzzy.FuzzyInteger(1, 10000000)
    name = factory.Faker("text", max_nb_chars=255)
    description = factory.Faker("text")
    url = factory.Faker("url")
    owner = factory.SubFactory(VCSAccountFactory)
    organization = factory.SubFactory(org_factories.Organization)
    forks_count = fuzzy.FuzzyInteger(1, 1000)
    stars_count = fuzzy.FuzzyInteger(1, 90000)
    created_at = factory.Faker("date_time", tzinfo=get_current_timezone())
    updated_at = factory.Faker("date_time", tzinfo=get_current_timezone())
    open_issues_count = fuzzy.FuzzyInteger(1, 1000)
    programming_languages = factory.Dict({fake.pystr(): fake.pyfloat() for _ in range(3)})

    class Meta:
        model = models.Repository
        django_get_or_create = ("vcs", "remote_id")


class Issue(factory.django.DjangoModelFactory):
    repository = factory.SubFactory(Repository)
    remote_id = fuzzy.FuzzyInteger(1, 10000000)
    title = factory.Faker("text")
    description = factory.Faker("text")
    state = fuzzy.FuzzyChoice(repo_enums.IssueState.choices)
    labels = ["bug", "back-end"]
    url = factory.Faker("url")
    created_at = factory.Faker("date_time", tzinfo=get_current_timezone())
    closed_at = factory.Faker("date_time", tzinfo=get_current_timezone())
    updated_at = factory.Faker("date_time", tzinfo=get_current_timezone())

    class Meta:
        model = models.Issue
        django_get_or_create = ("repository", "remote_id")
