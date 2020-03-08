import mock
from django.test import override_settings
from rest_framework import status
from rest_framework.reverse import reverse_lazy
from rest_framework.test import APITestCase
from users.exceptions import OAuthProviderNotFound


GITHUB_PROVIDER = {
    "client_id": "GITHUB_CLIENT_ID",
    "client_secret": "GITHUB_SECRET_KEY",
    "access_token_url": "https://github.com/login/oauth/access_token",
    "access_token_params": None,
    "authorize_url": "https://github.com/login/oauth/authorize",
    "authorize_params": None,
    "api_base_url": "https://api.github.com/",
    "client_kwargs": {"scope": "user:email"},
}


class ProviderNotFoundTestMixin:

    url_path = None

    def test_client_not_found(self):
        response = self.client.get(reverse_lazy(self.url_path, kwargs={"provider": "test_provider"}))
        detail = OAuthProviderNotFound("test_provider").detail
        self.assertTrue(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual({"detail": detail}, response.data)


@override_settings(AUTHLIB_OAUTH_CLIENTS={"github": GITHUB_PROVIDER})
class OAuthLoginViewTestCase(APITestCase, ProviderNotFoundTestMixin):

    url_path = "auth:login"

    def test_github_provider(self):
        response = self.client.get(reverse_lazy(self.url_path, kwargs={"provider": "github"}))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)


@override_settings(AUTHLIB_OAUTH_CLIENTS={"github": GITHUB_PROVIDER})
class OAuthCompleteViewTestCase(APITestCase, ProviderNotFoundTestMixin):

    url_path = "auth:complete"

    @mock.patch("authlib.integrations.django_client.integration.DjangoRemoteApp.authorize_access_token")
    def test_github_provider(self, patched):
        patched.return_value = "token"
        response = self.client.get(reverse_lazy(self.url_path, kwargs={"provider": "github"}))
        self.assertTrue(patched.call_count, 1)
        self.assertEqual(response.data["detail"], "token")
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
