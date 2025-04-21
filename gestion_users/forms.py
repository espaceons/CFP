# gestion_users/forms.py

from django import forms
from .models import CustomUser # Importe votre modèle utilisateur personnalisé

class UserProfileForm(forms.ModelForm):
    """
    Formulaire pour permettre à un utilisateur de modifier son profil.
    Basé sur le modèle CustomUser.
    """
    class Meta:
        model = CustomUser # Le modèle sur lequel est basé ce formulaire
        fields = [
            'first_name',
            'last_name',
            'email',
            'telephone',
            'adress',
            'date_naissance',
            # N'incluez pas le 'role', 'is_staff', etc. ici, ce n'est pas pour l'utilisateur lui-même.
        ]
        widgets = {
             # Exemple : utiliser un type date pour le champ date_naissance
             'date_naissance': forms.DateInput(attrs={'type': 'date'})
        }
        labels = {
             # Exemple : personnaliser un label si besoin
             # 'telephone': 'Numéro de téléphone'
        }

# Si vous avez d'autres formulaires pour la gestion des utilisateurs (signup, etc.), ils iraient ici.
# from django.contrib.auth.forms import UserCreationForm, UserChangeForm
# class CustomUserCreationForm(UserCreationForm): ...