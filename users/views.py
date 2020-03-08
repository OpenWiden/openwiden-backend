from authlib.common.errors import AuthlibBaseError
from authlib.integrations.django_client import OAuth
from rest_framework import views, permissions, status
from rest_framework.response import Response

from .exceptions import OAuthProviderNotFound
from .filters import OAuthCompleteFilter
from .utils import create_or_update_user

oauth = OAuth()
oauth.register("github")


class OAuthLoginView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        provider = kwargs["provider"]
        client = oauth.create_client(provider)

        if client is None:
            raise OAuthProviderNotFound(provider)

        return client.authorize_redirect(request)


class OAuthCompleteView(views.APIView):
    permission_classes = (permissions.AllowAny,)
    filter_backends = (OAuthCompleteFilter,)

    def get(self, request, *args, **kwargs):
        provider = kwargs["provider"]
        client = oauth.create_client(provider)

        if client is None:
            raise OAuthProviderNotFound(provider)

        try:
            token = client.authorize_access_token(request)
            user = self.request.user

            if user.is_anonymous:
                user = create_or_update_user(provider, client, token)

            msg, code = user.id, status.HTTP_200_OK
        except AuthlibBaseError as e:
            msg, code = e.description, status.HTTP_400_BAD_REQUEST

        return Response({"detail": msg}, code)
