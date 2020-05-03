import typing as t

# from django.utils.translation import gettext_lazy as _
# from django.db import models as m
from openwiden.repositories import models
from openwiden import enums
from openwiden.users import models as users_models
from openwiden.organizations import models as organizations_models


class Repository:
    @staticmethod
    def sync(
        version_control_service: str,
        remote_id: int,
        name: str,
        url: str,
        description: str = None,
        owner: users_models.User = None,
        organization: organizations_models.Organization = None,
        star_count: int = 0,
        open_issues_count: int = 0,
        forks_count: int = 0,
        programming_languages: t.List[str] = None,
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
            star_count=star_count,
            open_issues_count=open_issues_count,
            forks_count=forks_count,
            programming_languages=programming_languages,
            visibility=visibility,
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

    # @staticmethod
    # def all() -> m.QuerySet:
    #     """
    #     Returns all repositories QuerySet.
    #     """
    #     return models.Repository.objects.all()
    #
    # @staticmethod
    # def is_available_to_add(repository: models.Repository) -> t.Tuple[bool, t.Optional[str]]:
    #     """
    #     Returns repository status and message, that describes why it's not (if it is).
    #     """
    #     if repository.is_added is False:
    #         if repository.visibility == enums.VisibilityLevel.public:
    #             return True, None
    #         else:
    #             return False, _("{visibility} should be public.").format(visibility=repository.visibility)
    #     else:
    #         return False, _("{repository} already added.").format(repository=repository)
    #
    # @staticmethod
    # def added(visibility: str = enums.VisibilityLevel.public) -> m.QuerySet:
    #     """
    #     Returns filtered by "is_added" field repositories QuerySet.
    #     """
    #     return models.Repository.objects.filter(is_added=True, visibility=visibility)
    #
    # @staticmethod
    # def add(repository: models.Repository):
    #     """
    #     Adds the specified repository explicitly.
    #     """
    #     pass
    #
    # @staticmethod
    # def delete(repository: models.Repository):
    #     """
    #     Soft deletes the specified repository.
    #     """
    #     pass
