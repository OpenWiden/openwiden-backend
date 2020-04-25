import requests
import typing as t
from uuid import uuid4

from authlib.common.errors import AuthlibBaseError
from authlib.integrations.django_client import OAuth, DjangoRemoteApp
from django.contrib.auth.models import AnonymousUser
from django.core.files.base import ContentFile
from rest_framework.request import Request

from openwiden.users import models
from openwiden.users.services import exceptions, models as service_models


oauth = OAuth()
oauth.register("github")
oauth.register("gitlab")


class OAuthService:
    @staticmethod
    def get_client(provider: str) -> DjangoRemoteApp:
        """
        Returns authlib client instance or None if not found.
        """
        client = oauth.create_client(provider)
        if client is None:
            raise exceptions.ProviderNotFound(provider)
        return client

    @staticmethod
    def get_token(client: DjangoRemoteApp, request: Request) -> dict:
        """
        Returns token data from provider.
        """
        try:
            return client.authorize_access_token(request)
        except AuthlibBaseError as e:
            raise exceptions.TokenFetchException(e.description)

    @staticmethod
    def get_profile(provider: str, request: Request) -> "service_models.Profile":
        """
        Returns profile mapped cls with a data from provider's API.
        """
        client = OAuthService.get_client(provider)
        token = OAuthService.get_token(client, request)

        try:
            profile_data = client.get("user", token=token).json()
        except AuthlibBaseError as e:
            raise exceptions.ProfileRetrieveException(e.description)
        else:
            # Modify raw profile data if needed
            if provider == models.OAuth2Token.GITHUB_PROVIDER:
                # Do nothing
                pass
            elif provider == models.OAuth2Token.GITLAB_PROVIDER:
                profile_data["login"] = profile_data.pop("username")
            else:
                raise exceptions.ProviderNotImplemented(provider)

            return service_models.Profile(**profile_data, **token)

    @staticmethod
    def oauth(provider: str, user: t.Union[models.User, AnonymousUser], profile: service_models.Profile) -> models.User:
        """
        Returns user (new or existed) by provider and service provider profile data.
        """
        try:
            oauth2_token = models.OAuth2Token.objects.get(provider=provider, remote_id=profile.id)
        except models.OAuth2Token.DoesNotExist:
            # Handle case when oauth_token does not exists (first provider auth)
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
                    username=profile.login,
                    email=profile.email,
                    first_name=profile.first_name,
                    last_name=profile.last_name,
                )
                user.avatar.save(f"{uuid4()}.jpg", avatar)

            # Create new oauth token instance for user:
            # New if anonymous or existed if is authenticated.
            models.OAuth2Token.objects.create(
                user=user,
                provider=provider,
                remote_id=profile.id,
                login=profile.login,
                access_token=profile.access_token,
                token_type=profile.token_type or "",
                refresh_token=profile.refresh_token or "",
                expires_at=profile.expires_at,
            )
            return user
        else:
            # If user is authenticated, then check that oauth_token's user
            # is the same and if not -> just change it for current user.
            # Explanation:
            # github auth -> new user was created -> logout
            # gitlab auth -> new user was created and now we have a two user accounts,
            # but for the same user, that's wrong, because we want to have one account, but for
            # multiple services (github, gitlab etc.).
            # Now, if the second user will repeat auth with github, then oauth_token user will be
            # changed for the second user. Now we have one user account with two oauth_tokens as expected.
            if user.is_authenticated:
                if oauth2_token.user.username != user.username:
                    oauth2_token.user = user

            # Change oauth_token login if it's changed in github, gitlab etc.
            if oauth2_token.login != profile.login:
                oauth2_token.login = profile.login

            # Save changes for oauth_token
            oauth2_token.save()

            # Return oauth_token's user, because we can handle case when
            # user is not authenticated, but oauth_token for specified profile does exist.
            return oauth2_token.user
