import base64
import json

from allauth.socialaccount.models import SocialAccount
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.core.handlers.wsgi import WSGIRequest
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from liqpay3 import liqpay
from liqpay3.liqpay import LiqPay

from home.forms import NewSummaryForm, SignUpForm, VacancyForm
from home.models import Summary, User, Vacancy


def render_home(request: WSGIRequest) -> HttpResponse:
    if request.method == "GET":
        if request.user.is_authenticated:
            if request.user.city is None:
                return redirect(render_sign_up)

        return render(request, "pages/home.html", {"page": "home"})

    vacancies = Vacancy.objects.all()
    if request.POST.get("city"):
        vacancies = vacancies.filter(city=request.POST["city"])
    if request.POST.get("job_type"):
        vacancies = vacancies.filter(type=request.POST["job_type"])
    result = vacancies
    if request.POST.get("description"):
        result = []
        for vacancy in vacancies:
            if request.POST.get("description").lower() in vacancy.looking_for.lower():
                result.append(vacancy)
    return render(
        request, "pages/home.html", {"search_results": result, "form": request.POST}
    )


def render_sign_up(request: WSGIRequest) -> HttpResponse:
    if request.method == "GET":
        return render(request, "pages/sign_up.html", {"page": "user"})

    form = SignUpForm(request.POST)
    if not form.is_valid():
        return render(
            request,
            "pages/sign_up.html",
            {
                "page": "user",
                "form": {
                    "phone_number": form.phone_number,
                    "city": form.city,
                    "birthday": form.birthday,
                },
                "error": "Invalid form!",
            },
        )
    request.user.phone_number = form.cleaned_data["phone_number"]
    request.user.city = form.cleaned_data["city"]
    request.user.birthday = form.cleaned_data["birthday"]
    request.user.save()
    return redirect(render_home)


def render_vacancy(request: WSGIRequest, vacancy_id: int) -> HttpResponse:
    vacancy = Vacancy.objects.filter(id=vacancy_id).first()
    if not vacancy:
        return redirect(render_home)
    return render(request, "pages/vacancy.html", {"vacancy": vacancy})


def apply_vacancy(request: WSGIRequest, vacancy_id: int):
    if not request.user.is_authenticated:
        return redirect(render_home)

    vacancy = Vacancy.objects.filter(id=vacancy_id).first()
    if not vacancy:
        return redirect(render_home)
    vacancy.candidates.add(request.user)
    return redirect(f"/vacancy/@{vacancy_id}/")


def cancel_vacancy(request: WSGIRequest, vacancy_id: int):
    if not request.user.is_authenticated:
        return redirect(render_home)

    vacancy = Vacancy.objects.filter(id=vacancy_id).first()
    if not vacancy:
        return redirect(render_home)
    vacancy.candidates.remove(request.user)
    return redirect(f"/vacancy/@{vacancy_id}/")


def delete_vacancy(request: WSGIRequest, vacancy_id: int):
    vacancy = Vacancy.objects.filter(id=vacancy_id).first()

    if not request.user.is_authenticated or not vacancy or not request.user.email == vacancy.publisher:
        return redirect(render_home)

    vacancy.delete()
    return redirect(render_home)


def render_edit_vacancy(request: WSGIRequest, vacancy_id: int):
    if not request.user.is_authenticated or request.user.role != "E":
        return redirect(render_home)

    vacancy = Vacancy.objects.filter(id=vacancy_id).first()
    if not vacancy:
        return redirect(render_home)

    if request.method == "GET":
        return render(request, "pages/edit_vacancy.html", {"page": "user", "vacancy": vacancy})

    form = VacancyForm(request.POST)
    if not form.is_valid():
        return render(request, "pages/edit_vacancy.html", {"page": "user", "vacancy": vacancy})

    vacancy.title = form.cleaned_data.get("title")
    vacancy.city = form.cleaned_data.get("city")
    vacancy.type = form.cleaned_data.get("type")
    vacancy.looking_for = form.cleaned_data.get("looking_for")
    vacancy.description = form.cleaned_data.get("description")
    vacancy.thumbnail = form.cleaned_data.get("thumbnail")
    vacancy.save()
    return redirect(f"/vacancy/@{vacancy_id}/")


def render_profile(request: WSGIRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect(render_home)

    return render(request, "pages/profile.html", {"page": "user"})


def render_profile_personal(request: WSGIRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect(render_home)

    social_account = SocialAccount.objects.filter(user=request.user).first()
    return render(
        request,
        "pages/profile/personal.html",
        {
            "email_verified": social_account.extra_data.get("email_verified"),
            "picture": social_account.extra_data.get("picture"),
            "page": "user",
        },
    )


def render_profile_summary(request: WSGIRequest) -> HttpResponse:
    if not request.user.is_authenticated or request.user.role != "W":
        return redirect(render_home)
    summaries = Summary.objects.filter(user_id=request.user.id).all()
    return render(request, "pages/profile/summary.html", {"summaries": summaries, "page": "user"})


def new_profile_summary(request: WSGIRequest) -> HttpResponse:
    if not request.user.is_authenticated or request.user.role != "W":
        return redirect(render_home)
    if request.method == "GET":
        return render(request, "pages/profile/new_summary.html", {"page": "summary"})
    form = NewSummaryForm(request.POST)
    if not form.is_valid():
        return render(request, "pages/profile/new_summary.html", {"page": "summary"})
    summary = Summary(
        education=form.cleaned_data["education"],
        profession=form.cleaned_data["profession"],
        city=form.cleaned_data["city"],
        end_of_education=form.cleaned_data["end_of_education"],
        skills=form.cleaned_data["skills"],
        user_id=request.user.id,
    )
    summary.save()
    return redirect(render_profile_summary)


def render_summary(request: WSGIRequest, summary_id: int) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect(render_home)
    summary = Summary.objects.filter(id=summary_id).first()
    if not summary:
        return redirect(render_home)
    summary.add_view(request.user.id)
    return render(
        request,
        "pages/summary.html",
        {"summary": summary, "owner": User.objects.filter(id=summary.user_id).first(), "page": "summary"},
    )


def render_edit_profile_personal(request: WSGIRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect(render_home)

    if request.method == "GET":
        return render(request, "pages/profile/edit_personal.html", {"page": "user"})

    form = SignUpForm(request.POST)
    if not form.is_valid():
        return render(request, "pages/profile/edit_personal.html", {"page":"user", "error": "Невірна форма"})

    request.user.phone_number = form.cleaned_data.get("phone_number")
    request.user.city = form.cleaned_data.get("city")
    request.user.birthday = form.cleaned_data.get("birthday")
    if request.POST.get("role") == "E":
        request.user.role = "E"
    else:
        request.user.role = "W"
    request.user.save()
    return redirect(render_profile_personal)


def render_profile_vacancies(request: WSGIRequest):
    if not request.user.is_authenticated or request.user.role != "E":
        return redirect(render_home)
    vacancies = Vacancy.objects.filter(publisher=request.user.email).all()
    return render(request, "pages/profile/vacancies.html", {"vacancies": vacancies, "page": "user"})


def render_new_vacancy(request: WSGIRequest):
    if not request.user.is_authenticated or request.user.role != "E":
        return redirect(render_home)
    if request.method == "GET":
        return render(request, "pages/new_vacancy.html", {"page": "user"})

    form = VacancyForm(request.POST)
    if not form.is_valid():
        return render(request, "pages/new_vacancy.html", {"page": "user"})
    vacancy = Vacancy(publisher=request.user.email, creation_time=timezone.now())
    vacancy.title = form.cleaned_data.get("title")
    vacancy.city = form.cleaned_data.get("city")
    vacancy.type = form.cleaned_data.get("type")
    vacancy.looking_for = form.cleaned_data.get("looking_for")
    vacancy.description = form.cleaned_data.get("description")
    vacancy.thumbnail = form.cleaned_data.get("thumbnail")
    vacancy.save()
    return redirect(f"/vacancy/@{vacancy.id}/")


class PayView(TemplateView):
    template_name = "pages/pay.html"

    def get(self, request, *args, **kwargs):
        api = LiqPay("sandbox_i54579029593", "sandbox_EHx0Sf9PVpL9eqE4rcapQHGT2jJj1siOMQgGbPms")
        params = {
            'action'     : 'pay',
            'amount'     : '19',
            'currency'   : 'UAH',
            'description': 'Testing payment',
            'order_id'   : 'order_id_1',
            'version'    : '3',
            'sandbox'    : 1,  # sandbox mode, set to 1 to enable it
            'server_url' : 'https://django-server-production-fac1.up.railway.app/pay-callback/',  # url to callback view
        }
        signature = api.cnb_signature(params)
        data = base64.b64encode(json.dumps(params).encode('utf8'))
        return render(request, self.template_name, {'signature': signature, 'data': data})

@method_decorator(csrf_exempt, name='dispatch')
class PayCallbackView(View):
    def post(self, request, *args, **kwargs):
        liqpay = LiqPay("sandbox_i54579029593", "sandbox_EHx0Sf9PVpL9eqE4rcapQHGT2jJj1siOMQgGbPms")
        data = request.POST.get('data')
        signature = request.POST.get('signature')
        sign = liqpay.str_to_sign(
            "sandbox_EHx0Sf9PVpL9eqE4rcapQHGT2jJj1siOMQgGbPms" + data + "sandbox_EHx0Sf9PVpL9eqE4rcapQHGT2jJj1siOMQgGbPms")
        if sign == signature:
            print('callback is valid')
        response = liqpay.decode_data_from_str(data)
        print('callback data', response)
        return HttpResponse()
