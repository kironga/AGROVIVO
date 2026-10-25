from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
User=get_user_model()
class RegistrationForm(forms.ModelForm):
 password=forms.CharField(widget=forms.PasswordInput,validators=[validate_password],label="Password")
 class Meta:
  model=User
  fields=("username","email","first_name","last_name")
 def save(self,commit=True):
  user=super().save(commit=False); user.set_password(self.cleaned_data["password"])
  if commit: user.save()
  return user
