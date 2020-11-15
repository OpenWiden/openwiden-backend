import factory
from factory import fuzzy

from django.utils.timezone import get_current_timezone

from openwiden import enums
from openwiden.organizations import models
from openwiden.users.tests import factories as user_factories


class Organization(factory.django.DjangoModelFactory):
    vcs = fuzzy.FuzzyChoice(enums.VersionControlService.values)
    remote_id = factory.Faker("pyint")
    name = factory.Faker("company")
    description = factory.Faker("text")

    url = factory.Faker("url")
    avatar_url = factory.Faker("url")

    created_at = factory.Faker("date_time", tzinfo=get_current_timezone())

    class Meta:
        model = models.Organization
        django_get_or_create = ("vcs", "remote_id")


class Member(factory.django.DjangoModelFactory):
    organization = factory.SubFactory(Organization)
    vcs_account = factory.SubFactory(user_factories.VCSAccountFactory)
    is_admin = factory.Faker("pybool")

    class Meta:
        model = models.Member
        django_get_or_create = ("vcs_account", "organization")
