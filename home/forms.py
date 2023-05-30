from django import forms


class SignUpForm(forms.Form):
    phone_number = forms.CharField(max_length=16, required=True)
    city = forms.CharField(max_length=64, required=True)
    birthday = forms.DateField(required=True)


class NewSummaryForm(forms.Form):
    education = forms.CharField(max_length=1, required=True)
    profession = forms.CharField(max_length=64, required=True)
    city = forms.CharField(max_length=64, required=True)
    end_of_education = forms.DateField(required=True)
    skills = forms.CharField(max_length=256, required=True)


class VacancyForm(forms.Form):
    title = forms.CharField(max_length=128, required=True)
    city = forms.CharField(max_length=64, required=True)
    type = forms.CharField(max_length=1, required=True)
    looking_for = forms.CharField(max_length=32, required=True)
    description = forms.CharField(max_length=10_000, required=True)
    thumbnail = forms.CharField(max_length=512, required=True)
