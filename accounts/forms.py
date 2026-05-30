from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

User = get_user_model()


class GirisForm(AuthenticationForm):
    username = forms.CharField(
        label="Kullanıcı adı",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Kullanıcı adınız",
                "autocomplete": "username",
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        label="Şifre",
        widget=forms.PasswordInput(
            attrs={"placeholder": "••••••••", "autocomplete": "current-password"}
        ),
    )


class KullaniciOlusturForm(UserCreationForm):
    first_name = forms.CharField(label="Ad", max_length=150, required=True)
    last_name = forms.CharField(label="Soyad", max_length=150, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"placeholder": "ör. ahmet.yilmaz"})
        self.fields["first_name"].widget.attrs.update({"placeholder": "Ad"})
        self.fields["last_name"].widget.attrs.update({"placeholder": "Soyad"})
