import json
from enum import Enum
from logging import getLogger
from typing import Optional, Union
from uuid import uuid4

import requests
from authlib.common.errors import AuthlibBaseError
from authlib.integrations.django_client import OAuth, DjangoRemoteApp
from django.contrib.auth.models import AnonymousUser
from django.core.files.base import ContentFile
from django_q.tasks import async_task
from django_redis import get_redis_connection
from pydantic import BaseModel, Field
from rest_framework.request import Request
from rest_framework_simplejwt.tokens import RefreshToken

from openwiden.repositories import (
    services as repositories_services,
    enums as repository_enums,
)
from openwiden.exceptions import ServiceException

from . import models, serializers, exceptions

log = getLogger(__name__)


class WebsocketMessageObjectType(str, Enum):
    REPOSITORY = "repository"


class WebsocketMessageObject(BaseModel):
    id_: str = Field(alias="id")
    type_: WebsocketMessageObjectType = Field(alias="type")


class RepositoryMessageObject(WebsocketMessageObject):
    state: repository_enums.RepositoryState


class WebsocketMessage(BaseModel):
    message: str
    object_: Optional[WebsocketMessageObject] = Field(alias="object")


def repository_message_factory(
    *, message: str, repository_id: str, state: repository_enums.RepositoryState,
) -> WebsocketMessage:
    return WebsocketMessage(
        message=message,
        object=RepositoryMessageObject(id=str(repository_id), type=WebsocketMessageObjectType.REPOSITORY, state=state,),
    )


RepositoryMessage = repository_message_factory


class Token:
    def __init__(
        self, access_token: str, token_type: str, refresh_token: str = None, expires_at: int = None, **kwargs,
    ) -> None:
        self.access_token = access_token
        self.token_type = token_type
        self.refresh_token = refresh_token
        self.expires_at = expires_at


class Profile:
    def __init__(
        self,
        id: int,
        login: str,
        name: str,
        email: str,
        avatar_url: str,
        token: Token,
        split_name: bool = True,
        **kwargs,
    ):
        self.id: int = id
        self.login = login
        self._name = name
        self.email = email
        self.first_name = ""
        self.last_name = ""
        self.avatar_url = avatar_url
        self.token = token

        if split_name and self._name:
            self.first_name, sep, self.last_name = self._name.partition(" ")

    @classmethod
    def _parse_github_profile_json(cls, data: dict, token_data: dict) -> "Profile":
        token = Token(**token_data)
        return Profile(**data, token=token)

    @classmethod
    def _parse_gitlab_profile_json(cls, data: dict, token_data: dict) -> "Profile":
        data["login"] = data.pop("username", None)
        token = Token(**token_data)
        return Profile(**data, token=token)

    @classmethod
    def from_json(cls, vcs: str, data: dict, token: dict) -> "Profile":
        parse_function = getattr(cls, f"_parse_{vcs}_profile_json")
        return parse_function(data, token)


oauth_client = OAuth()
oauth_client.register("github")
oauth_client.register("gitlab")


def get_jwt_tokens(user: models.User) -> dict:
    """
    Returns JWT tokens for specified user.
    """
    refresh = RefreshToken.for_user(user)
    return dict(access=str(refresh.access_token), refresh=str(refresh))


def get_client(*, vcs: str) -> DjangoRemoteApp:
    """
    Returns authlib client instance or None if not found.
    """
    client = oauth_client.create_client(vcs)
    if client is None:
        raise exceptions.VCSProviderNotFound(vcs=vcs)
    return client


def get_user_profile(*, vcs: str, request: Request) -> Profile:
    client = get_client(vcs=vcs)

    try:
        token = client.authorize_access_token(request)
    except AuthlibBaseError as e:
        raise exceptions.AuthlibError(error_description=e.description)

    try:
        profile_data = client.get("user", token=token).json()

        # Also check if email does not exist and get it from API
        # Useful for GitHub, when "private email" option is ON.
        if profile_data.get("email") is None:
            emails = client.get("user/emails", token=token).json()
            profile_data["email"] = emails[0]["email"]

    except AuthlibBaseError as e:
        raise exceptions.AuthlibError(error_description=e.description)
    else:
        return Profile.from_json(vcs=vcs, data=profile_data, token=token)


def oauth(*, vcs: str, user: Union[models.User, AnonymousUser], request: Request) -> models.User:
    """
    Returns user (new or existed) by provider and service provider profile data.
    """
    profile = get_user_profile(vcs=vcs, request=request)

    try:
        vcs_account = models.VCSAccount.objects.get(vcs=vcs, remote_id=profile.id)
    except models.VCSAccount.DoesNotExist:
        # Handle case when vcs_account does not exists (first provider auth)
        # Check if user is not authenticated and create it first.
        if user.is_anonymous:
            # Check if username is already exists with profile's login
            # and create unique (login + hex) if exists else do nothing.
            qs = models.User.objects.filter(username=profile.login)
            if qs.exists():
                profile.login = f"{profile.login}_{uuid4().hex}"

            # Download user's avatar from service
            avatar = ContentFile(requests.get(profile.avatar_url).content)

            # Create new user and save avatar
            user = models.User.objects.create(
                username=profile.login, email=profile.email, first_name=profile.first_name, last_name=profile.last_name,
            )
            user.avatar.save(f"{uuid4()}.jpg", avatar)

        # Create new oauth token instance for user:
        # New if anonymous or existed if is authenticated.
        create_vcs_account(
            user=user,
            vcs=vcs,
            remote_id=profile.id,
            login=profile.login,
            access_token=profile.token.access_token,
            token_type=profile.token.token_type,
            refresh_token=profile.token.refresh_token,
            expires_at=profile.token.expires_at,
        )
        return user
    else:
        # If user is authenticated, then check that vcs_account's user
        # is the same and if not -> just change it for current user.
        # Explanation:
        # github auth -> new user was created -> logout
        # gitlab auth -> new user was created and now we have a two user accounts,
        # but for the same user, that's wrong, because we want to have one account, but for
        # multiple services (github, gitlab etc.).
        # Now, if the second user will repeat auth with github, then vcs_account user will be
        # changed for the second user. Now we have one user account with two oauth_tokens as expected.
        update_fields = ("access_token", "token_type", "refresh_token", "expires_at")

        # Update token data fields
        vcs_account.access_token = profile.token.access_token
        vcs_account.token_type = profile.token.token_type
        vcs_account.refresh_token = profile.token.refresh_token
        vcs_account.expires_at = profile.token.expires_at

        # Change user if current authenticated user is not equals account user
        if user.is_authenticated:
            if vcs_account.user.username != user.username:
                vcs_account.user = user
                update_fields += ("user",)

        # Change vcs_account login if it's changed in github, gitlab etc.
        if vcs_account.login != profile.login:
            vcs_account.login = profile.login
            update_fields += ("login",)

        # Save changes for vcs_account
        if update_fields:
            vcs_account.save(update_fields=update_fields)

        # Return vcs_account's user, because we can handle case when
        # user is not authenticated, but vcs_account for specified profile does exist.
        return vcs_account.user


def create_vcs_account(
    *,
    user: models.User,
    vcs: str,
    remote_id: int,
    login: str,
    access_token: str,
    token_type: str = None,
    refresh_token: str = None,
    expires_at: int = None,
):
    """
    Validate specified data and create new oauth token instance.
    Also trigger new actions for a new created token.
    """
    data = dict(
        user=user.id,
        vcs=vcs,
        remote_id=remote_id,
        login=login,
        access_token=access_token,
        token_type=token_type,
        refresh_token=refresh_token,
        expires_at=expires_at,
    )
    serializer = serializers.CreateVCSAccountSerializer(data=data)

    # Save vcs account instance
    if serializer.is_valid():
        vcs_account = serializer.save()
        async_task(repositories_services.sync_user_repositories, vcs_account=vcs_account)
        return vcs_account
    else:
        raise exceptions.InvalidVCSAccount(serializer_errors=serializer.errors)


def send_notification(*, user: models.User, message: Union[WebsocketMessage, ServiceException]) -> None:
    if isinstance(message, WebsocketMessage):
        message = json.dumps(message.dict(by_alias=True))
    elif isinstance(message, ServiceException):
        message = message.json_dumped_detail
    else:
        raise ValueError(
            f"send_notification received message '{message}' of type {type(message)} "
            f"instead of expected type {WebsocketMessage} or {ServiceException}"
        )

    log.info(f"[Service] sending notification for user {user} with a message '{message}'")

    redis = get_redis_connection()
    redis.publish(str(user.id), message)
