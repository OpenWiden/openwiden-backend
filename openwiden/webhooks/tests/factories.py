import factory

from openwiden.webhooks import models
from openwiden.repositories.tests import factories


class RepositoryWebhookFactory(factory.django.DjangoModelFactory):
    repository = factory.SubFactory(factories.Repository)
    remote_id = factory.Faker("pyint")
    url = factory.Faker("url")
    secret = factory.Faker("pystr")
    issue_events_enabled = factory.Faker("pybool")
    created_at = factory.Faker("date_time")
    updated_at = factory.Faker("date_time")

    class Meta:
        model = models.RepositoryWebhook
