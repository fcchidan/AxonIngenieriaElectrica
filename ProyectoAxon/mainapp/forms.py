from django import forms 
from django.core import validators
from blog.models import DireccionEnvio


from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']



class DireccionEnvioForm(forms.ModelForm):
    class Meta:
        model = DireccionEnvio
        fields = ['direccion', 'ciudad', 'codigo_postal', 'telefono', 'correo']

