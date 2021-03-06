from rest_framework_nested import routers
from django.urls import path, include

from openwiden.repositories import views as repository_views
from openwiden.users import views as users_views
from openwiden.webhooks import urls as webhook_urls

app_name = "v1"

router = routers.DefaultRouter()

# Repositories
router.register("repositories", repository_views.Repository, basename="repository")
repository_router = routers.NestedSimpleRouter(router, "repositories", lookup="repository")
repository_router.register("issues", repository_views.Issue, basename="repository-issue")
router.register("user/repositories", repository_views.UserRepositories, basename="user-repository")

# Users
router.register("users", users_views.UserViewSet, basename="user")

auth_urlpatterns = [
    path("auth/login/<str:vcs>/", users_views.oauth_login_view, name="auth-login"),
    path("auth/complete/<str:vcs>/", users_views.oauth_complete_view, name="auth-complete"),
    path("auth/refresh_token/", users_views.token_refresh_view, name="auth-refresh_token"),
    path("user/", users_views.user_me_view, name="user-me"),
]

urlpatterns = [
    path("webhooks/", include(webhook_urls, namespace="webhooks")),
    path("programming_languages/", repository_views.programming_languages_view, name="programming_languages"),
]

urlpatterns += auth_urlpatterns
urlpatterns += router.urls
urlpatterns += repository_router.urls
