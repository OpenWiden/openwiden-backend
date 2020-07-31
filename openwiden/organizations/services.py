from typing import Tuple

from openwiden import enums, vcs_clients
from openwiden.organizations import models
from openwiden.users import models as users_models


def sync_github_organization_member(
    *, organization: models.Organization, vcs_account: users_models.VCSAccount, is_admin: bool,
) -> Tuple[models.Member, bool]:
    return models.Member.objects.update_or_create(
        organization=organization, vcs_account=vcs_account, defaults=dict(is_admin=is_admin),
    )


def sync_github_organization(
    *, organization: vcs_clients.github.models.Organization,
) -> Tuple[models.Organization, bool]:
    return models.Organization.objects.update_or_create(
        vcs=enums.VersionControlService.GITHUB,
        remote_id=organization.organization_id,
        defaults=dict(
            name=organization.login,
            description=organization.description,
            url=organization.html_url,
            avatar_url=organization.avatar_url,
            created_at=organization.created_at,
        ),
    )
