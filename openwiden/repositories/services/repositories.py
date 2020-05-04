import typing as t

from django.utils.translation import gettext_lazy as _
from django.db import models as m

from datetime import datetime

from django_q.tasks import async_task

from openwiden.repositories import models
from openwiden import enums
from openwiden.users import models as users_models, services as users_services
from openwiden.organizations import models as organizations_models
from openwiden.services import remote, exceptions


class Repository:
    @staticmethod
    def sync(
        version_control_service: str,
        remote_id: int,
        name: str,
        url: str,
        created_at: datetime,
        updated_at: datetime,
        description: str = None,
        owner: users_models.User = None,
        organization: organizations_models.Organization = None,
        stars_count: int = 0,
        open_issues_count: int = 0,
        forks_count: int = 0,
        programming_languages: dict = None,
        visibility: str = enums.VisibilityLevel.private,
    ) -> t.Tuple[models.Repository, bool]:
        """
        Synchronizes repository with specified data (update or create).
        """
        fields = dict(
            name=name,
            url=url,
            description=description,
            owner=owner,
            organization=organization,
            stars_count=stars_count,
            open_issues_count=open_issues_count,
            forks_count=forks_count,
            programming_languages=programming_languages,
            visibility=visibility,
            created_at=created_at,
            updated_at=updated_at,
        )

        # Try to create or update repository
        try:
            repository, created = (
                models.Repository.objects.get(version_control_service=version_control_service, remote_id=remote_id),
                False,
            )
        except models.Repository.DoesNotExist:
            repository, created = (
                models.Repository.objects.create(
                    version_control_service=version_control_service, remote_id=remote_id, is_added=False, **fields,
                ),
                True,
            )
        else:
            # Update values if repository exist
            for k, v in fields.items():
                setattr(repository, k, v)
            repository.save()

        # TODO: notify
        if created:
            pass

        return repository, created

    @staticmethod
    def add(repository: models.Repository, user: users_models.User) -> str:
        oauth_token = users_services.OAuthToken.get_token(user, repository.version_control_service)

        # Check if repository is already added and raise an error if yes
        if repository.is_added:
            raise exceptions.ServiceException(_("Repository already added."))
        elif repository.visibility == enums.VisibilityLevel.private:
            raise exceptions.ServiceException(_("Repository is private and cannot be added."))

        # Set is_added True for now, but save in sync action (if success)
        repository.is_added = True

        # Call repository sync action
        remote_service = remote.get_service(oauth_token)
        return async_task(remote_service.sync_repository, repository=repository)

    @staticmethod
    def get_user_repos(user: users_models.User) -> m.QuerySet:
        return models.Repository.objects.filter(m.Q(owner=user) | m.Q(organization__member__user=user))

    @staticmethod
    def added(visibility: str = enums.VisibilityLevel.public) -> m.QuerySet:
        """
        Returns repositories QuerySet filtered by "is_added" field and optional visibility (default is public).
        """
        return models.Repository.objects.filter(is_added=True, visibility=visibility)

    @classmethod
    def added_and_public(cls) -> m.QuerySet:
        """
        Returns added and public visible repositories also known as "OpenWiden".
        """
        return cls.added(enums.VisibilityLevel.public)

    @staticmethod
    def delete(repository: models.Repository):
        pass
