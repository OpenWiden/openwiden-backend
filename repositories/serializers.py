from rest_framework import serializers

from repositories import models


class ProgrammingLanguage(serializers.ModelSerializer):
    class Meta:
        model = models.ProgrammingLanguage
        fields = ("id", "name")


class RepositorySerializer(serializers.ModelSerializer):
    version_control_service = serializers.CharField(source="version_control_service.host")

    class Meta:
        model = models.Repository
        fields = (
            "id",
            "version_control_service",
            "name",
            "description",
            "url",
            "star_count",
            "open_issues_count",
            "forks_count",
            "created_at",
            "updated_at",
            "programming_language",
        )


class IssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Issue
        fields = (
            "id",
            "title",
            "description",
            "state",
            "labels",
            "url",
            "created_at",
            "closed_at",
            "updated_at",
        )
