from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponseNotFound
from rest_framework.decorators import api_view
from rest_framework.response import Response

from home.models import EDUCATIONS_MAP, ROLES, Summary, User, Vacancy, WORK_TYPES
from home.tests import CITY_NAMES, get_city_name
from .serializers import SummarySerializer, UserSerializer, VacancySerializer


@api_view(["GET"])
def get_routes(request: WSGIRequest):
    return Response({
        "/": "This page",
        "/get_cities/": "Get list of all possible cities",
        "/get_educations/": "Get list of all possible educations",
        "/get_roles/": "Get list of all possible roles",
        "/get_work_types/": "Get list of all possible work types",
        "/get_user/": "Get the current authenticated user",
        "/get_summaries/": "Get all summaries of the authenticated user",
        "/fetch_summaries/<USER_EMAIL>": "Get all summaries of a user",
        "/get_vacancies/": "Get all vacancies",
        "/get_city_name/<CITY_ID>/": "Get the name (in Ukrainian) of a city using its ID",
    })


@api_view(["GET"])
def get_cities(request: WSGIRequest):
    return Response({
        "cities": [
            {
                "id": city,
                "name": CITY_NAMES.get(city),
            } for city in CITY_NAMES.keys()
        ]
    })


@api_view(["GET"])
def get_educations(request: WSGIRequest):
    return Response({
        "educations": [
            {
                "id": education,
                "name": EDUCATIONS_MAP.get(education),
            } for education in EDUCATIONS_MAP.keys()
        ]
    })


@api_view(["GET"])
def get_roles(request: WSGIRequest):
    return Response({
        "roles": [
            {
                "id": role[0],
                "name": role[1],
            } for role in ROLES
        ]
    })


@api_view(["GET"])
def get_work_types(request: WSGIRequest):
    return Response({
        "work_types": [
            {
                "id": work_type[0],
                "name": work_type[1],
            } for work_type in WORK_TYPES
        ]
    })


@api_view(["GET"])
def get_user(request: WSGIRequest):
    if not request.user.is_authenticated:
        return HttpResponseNotFound({
            "message": "Request is not authenticated. Please, log-in using Google before continuing!"
        })
    return Response(UserSerializer(User.objects.filter(id=request.user.id).first(), many=False).data)


@api_view(["GET"])
def get_summaries(request: WSGIRequest):
    if not request.user.is_authenticated:
        return HttpResponseNotFound({
            "message": "Request is not authenticated. Please, log-in using Google before continuing!"
        })

    return Response(SummarySerializer(Summary.objects.filter(user_id=request.user.id).all(), many=True).data)


@api_view(["GET"])
def fetch_summaries(request: WSGIRequest, user: str):
    return Response(SummarySerializer(Summary.objects.filter(user_id=User.objects.filter(email=user).first().id).all(), many=True).data)


@api_view(["GET"])
def get_vacancies(request: WSGIRequest):
    if not request.user.is_authenticated:
        return HttpResponseNotFound({
            "message": "Request is not authenticated. Please, log-in using Google before continuing!"
        })

    return Response(VacancySerializer(Vacancy.objects.all(), many=True).data)


@api_view(["GET"])
def get_city(request: WSGIRequest, city: str):
    return Response({
        "city": city,
        "name": get_city_name(city)
    })
