from rest_framework import serializers
from home.models import User, Vacancy, Summary


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "phone_number", "city", "birthday", "photo", "role", "is_staff", "is_active", "is_superuser", "is_active", "last_login"]


class VacancySerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField("serialized_type")
    city_name = serializers.SerializerMethodField("serialized_city")
    candidates = serializers.SerializerMethodField("serialized_candidates")

    def serialized_type(self, obj: Vacancy):
        return obj.get_type()

    def serialized_city(self, obj: Vacancy):
        return obj.get_city()

    def serialized_candidates(self, obj: Vacancy):
        return obj.get_candidates()

    class Meta:
        model = Vacancy
        fields = ["publisher", "title", "description", "thumbnail", "type", "city", "city_name", "looking_for", "candidates", "creation_time"]


class SummarySerializer(serializers.ModelSerializer):
    education_name = serializers.SerializerMethodField("serialized_education")
    view_count = serializers.SerializerMethodField("serialized_views")
    city_name = serializers.SerializerMethodField("serialized_city")

    def serialized_education(self, obj: Summary):
        return obj.get_education()

    def serialized_views(self, obj: Summary):
        return obj.get_view_count()

    def serialized_city(self, obj):
        return obj.get_city()

    class Meta:
        model = Summary
        fields = ["id", "education", "education_name", "profession", "end_of_education", "skills", "city", "city_name", "view_count"]
