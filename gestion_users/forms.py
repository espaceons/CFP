# gestion_users/forms.py

from django import forms
from .models import CustomUser # Importe votre modèle utilisateur personnalisé

from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import gettext_lazy as _

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





class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField( label=_("Nom d'utilisateur ou Email"), widget=forms.TextInput(attrs={'autofocus': True}))
    password = forms.CharField( label=_("Mot de passe"), strip=False, widget=forms.PasswordInput)
    remember_me = forms.BooleanField(
        label="Se souvenir de moi",
        required=False, # Ce champ n'est pas obligatoire
        widget=forms.CheckboxInput # Affiche une checkbox
    )
    
    error_messages = {
        'invalid_login': _(
            "Veuillez saisir un %(username)s et un mot de passe valides. "
            "Remarque : les champs peuvent être sensibles à la casse."
        ),
        'inactive': _("Ce compte est inactif."),
    }
    
    
# --- Formulaire pour la création d'utilisateur ---
class CustomUserCreationForm(UserCreationForm):
    """
    Formulaire personnalisé pour créer un nouvel utilisateur CustomUser.
    Inclut les champs supplémentaires du modèle CustomUser.
    """
    class Meta(UserCreationForm.Meta):
        model = CustomUser # Utilise votre modèle CustomUser
        fields = UserCreationForm.Meta.fields + (
            'first_name',
            'last_name',
            'email',
            'telephone',
            'adress',
            'date_naissance',
            # N'incluez PAS le champ 'role' dans un formulaire d'inscription public,
            # sauf si vous gérez explicitement qui peut s'inscrire avec quel rôle (complexe et non recommandé).
            # Le rôle sera défini par défaut dans le modèle (STUDENT) ou géré dans la vue.
        )
        # Vous pouvez ajouter des widgets ou des labels personnalisés ici si nécessaire pour ces champs
        widgets = {
             'date_naissance': forms.DateInput(attrs={'type': 'date'})
        }
        # labels = {
        #      'telephone': 'Numéro de téléphone',
        #      'adress': 'Adresse',
        #      'date_naissance': 'Date de naissance',
        # }

    # Optionnel : Vous pouvez override la méthode save si vous avez besoin de logique supplémentaire
    # def save(self, commit=True):
    #     user = super().save(commit=False)
    #     # Vous pourriez définir le rôle ici si vous ne voulez pas utiliser le default du modèle
    #     # user.role = CustomUser.UserRole.STUDENT # Force le rôle à étudiant
    #     if commit:
    #         user.save()
    #     return user