from allauth.socialaccount.models import SocialAccount
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from liqpay3.liqpay import LiqPay

from headhunter.urls import GLOBAL_TOKEN
from home.forms import NewSummaryForm, SignUpForm, VacancyForm
from home.models import Summary, User, Vacancy

api = LiqPay("sandbox_i54579029593", "sandbox_EHx0Sf9PVpL9eqE4rcapQHGT2jJj1siOMQgGbPms")
LIQPAY = LiqPay(
    "sandbox_i54579029593", "sandbox_EHx0Sf9PVpL9eqE4rcapQHGT2jJj1siOMQgGbPms"
)


def render_home(request: WSGIRequest) -> HttpResponse:
    if request.method == "GET":
        if request.user.is_authenticated:
            if request.user.city is None:
                return redirect(render_sign_up)

            if request.session.get("ORDER_ID"):
                response: dict = api.api(
                    "request/",
                    {
                        "action": "status",
                        "version": "3",
                        "order_id": request.session.get("ORDER_ID"),
                    },
                )
                if response.get("result") == "ok":
                    order_id: str = request.session.get("ORDER_ID").split("@")[1]
                    request.session["ORDER_ID"] = None
                    vacancy: Vacancy = (
                        None
                        if not order_id.isnumeric()
                        else Vacancy.objects.filter(id=int(order_id)).first()
                    )
                    if vacancy:
                        vacancy.is_premium = True
                        vacancy.save()
                    return render(
                        request,
                        "pages/home.html",
                        {
                            "page": "home",
                            "order_info": {
                                "vacancy": vacancy,
                                "extra": response,
                            },
                        },
                    )

        return render(request, "pages/home.html", {"page": "home"})

    vacancies = Vacancy.objects.all()
    if request.POST.get("city"):
        vacancies = vacancies.filter(city=request.POST["city"])
    if request.POST.get("job_type"):
        vacancies = vacancies.filter(type=request.POST["job_type"])
    result = [v for v in vacancies]
    if request.POST.get("description"):
        result = []
        for vacancy in vacancies:
            if request.POST.get("description").lower() in vacancy.looking_for.lower():
                result.append(vacancy)
    result.sort(key=lambda v: v.is_premium, reverse=True)
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
    if request.user.is_authenticated:
        if request.user.city is None:
            return redirect(render_sign_up)
    vacancy = Vacancy.objects.filter(id=vacancy_id).first()
    if not vacancy:
        return redirect(render_home)
    request.session["ORDER_ID"] = f"VACANCY:{GLOBAL_TOKEN}@{vacancy_id}"
    extra = {}
    if not vacancy.is_premium and request.user.is_authenticated and request.user.email == vacancy.publisher:
        extra = {
            "form": LIQPAY.cnb_form(
                {
                    "action": "pay",
                    "amount": "200",
                    "currency": "UAH",
                    "description": f"Активувати Преміум для {vacancy.title}",
                    "order_id": f"VACANCY:{GLOBAL_TOKEN}@{vacancy_id}",
                    "version": "3",
                    "sandbox": 0,
                    "server_url": "https://django-server-production-fac1.up.railway.app/",
                }
            )
            .replace("""accept-charset="utf-8">""", 'accept-charset="utf-8">')
            .replace(
                """<input type="image" src="//static.liqpay3.ua/buttons/p1ru.radius.png" name="btn_text" />""",
                '<button type="submit" class="button premium">'
                '<i class="fi fi-sr-crown"></i>'
                "<span>Активувати Преміум</span>"
                "</button>",
            )
        }
    return render(request, "pages/vacancy.html", {"vacancy": vacancy, **extra})


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

    if (
        not request.user.is_authenticated
        or not vacancy
        or not request.user.email == vacancy.publisher
    ):
        return redirect(render_home)

    vacancy.delete()
    return redirect(render_home)


def render_edit_vacancy(request: WSGIRequest, vacancy_id: int):
    if request.user.is_authenticated:
        if request.user.city is None:
            return redirect(render_sign_up)
    if not request.user.is_authenticated or request.user.role != "E":
        return redirect(render_home)

    vacancy = Vacancy.objects.filter(id=vacancy_id).first()
    if not vacancy:
        return redirect(render_home)

    if request.method == "GET":
        return render(
            request, "pages/edit_vacancy.html", {"page": "user", "vacancy": vacancy}
        )

    form = VacancyForm(request.POST)
    if not form.is_valid():
        return render(
            request, "pages/edit_vacancy.html", {"page": "user", "vacancy": vacancy}
        )

    vacancy.title = form.cleaned_data.get("title")
    vacancy.city = form.cleaned_data.get("city")
    vacancy.type = form.cleaned_data.get("type")
    vacancy.looking_for = form.cleaned_data.get("looking_for")
    vacancy.description = form.cleaned_data.get("description")
    vacancy.thumbnail = form.cleaned_data.get("thumbnail")
    vacancy.save()
    return redirect(f"/vacancy/@{vacancy_id}/")


def render_profile(request: WSGIRequest) -> HttpResponse:
    if request.user.is_authenticated:
        if request.user.city is None:
            return redirect(render_sign_up)
    if not request.user.is_authenticated:
        return redirect(render_home)

    return render(request, "pages/profile.html", {"page": "user"})


def render_profile_personal(request: WSGIRequest) -> HttpResponse:
    if request.user.is_authenticated:
        if request.user.city is None:
            return redirect(render_sign_up)
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
    if request.user.is_authenticated:
        if request.user.city is None:
            return redirect(render_sign_up)
    if not request.user.is_authenticated or request.user.role != "W":
        return redirect(render_home)
    summaries = Summary.objects.filter(user_id=request.user.id).all()
    return render(
        request, "pages/profile/summary.html", {"summaries": summaries, "page": "user"}
    )


def new_profile_summary(request: WSGIRequest) -> HttpResponse:
    if request.user.is_authenticated:
        if request.user.city is None:
            return redirect(render_sign_up)
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
    if request.user.is_authenticated:
        if request.user.city is None:
            return redirect(render_sign_up)
    if not request.user.is_authenticated:
        return redirect(render_home)
    summary = Summary.objects.filter(id=summary_id).first()
    if not summary:
        return redirect(render_home)
    summary.add_view(request.user.id)
    return render(
        request,
        "pages/summary.html",
        {
            "summary": summary,
            "owner": User.objects.filter(id=summary.user_id).first(),
            "page": "summary",
        },
    )


def render_edit_profile_personal(request: WSGIRequest) -> HttpResponse:
    if request.user.is_authenticated:
        if request.user.city is None:
            return redirect(render_sign_up)
    if not request.user.is_authenticated:
        return redirect(render_home)

    if request.method == "GET":
        return render(request, "pages/profile/edit_personal.html", {"page": "user"})

    form = SignUpForm(request.POST)
    if not form.is_valid():
        return render(
            request,
            "pages/profile/edit_personal.html",
            {"page": "user", "error": "Невірна форма"},
        )

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
    if request.user.is_authenticated:
        if request.user.city is None:
            return redirect(render_sign_up)
    if not request.user.is_authenticated or request.user.role != "E":
        return redirect(render_home)
    vacancies = Vacancy.objects.filter(publisher=request.user.email).all()
    return render(
        request,
        "pages/profile/vacancies.html",
        {"vacancies": vacancies, "page": "user"},
    )


def render_new_vacancy(request: WSGIRequest):
    if request.user.is_authenticated:
        if request.user.city is None:
            return redirect(render_sign_up)
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
