# gestion_users/forms.py

from django import forms
from .models import CustomUser, UserRole # Importe votre modèle utilisateur personnalisé

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
            'photo',
            # N'incluez pas le 'role', 'is_staff', etc. ici, ce n'est pas pour l'utilisateur lui-même.
        ]
        widgets = {
             # Exemple : utiliser un type date pour le champ date_naissance
             'date_naissance': forms.DateInput(attrs={'type': 'date'}),
             'adress': forms.Textarea(attrs={'rows': 4}), # Exemple de widget pour l'adresse
        }
        labels = {
             # Exemple : personnaliser un label si besoin
             # 'telephone': 'Numéro de téléphone'
             'photo': 'Photo de profil', # Label pour le champ photo
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
    Inclut les champs supplémentaires du modèle CustomUser ET le champ photo.
    """
    class Meta(UserCreationForm.Meta):
        model = CustomUser # Utilise votre modèle CustomUser
        # --- AJOUTEZ 'photo' à la liste des champs pour l'inscription ---
        fields = UserCreationForm.Meta.fields + (
            'first_name',
            'last_name',
            'email',
            'telephone',
            'adress',
            'date_naissance',
            'photo', # <-- PHOTO ICI pour le formulaire d'inscription
            'role', # <-- CHAMP ROLE ICI dans Meta.fields
        )
        # --- Fin des champs ---

        # Vous pouvez ajouter des widgets ou des labels personnalisés ici
        widgets = {
             'date_naissance': forms.DateInput(attrs={'type': 'date'}),
             'adress': forms.Textarea(attrs={'rows': 4}), # Exemple de widget pour l'adresse
        }
        labels = {
             'photo': 'Photo de profil', # Label pour le champ photo
             'role': 'Je suis un(e)', # Label personnalisé pour le rôle
             # Ajoutez des labels pour les autres champs si vous voulez personnaliser #
         }
        
        # --- DÉFINISSEZ LA MÉTHODE __init__ POUR LIMITER LES CHOIX DU CHAMP ROLE ---
        def __init__(self, *args, **kwargs):
            # Appelle la méthode __init__ de la classe parente (UserCreationForm)
            super().__init__(*args, **kwargs)

            # --- Limite les choix du champ 'role' ---
            # Accède au champ 'role' dans les champs du formulaire ('self.fields')
            # Définit ses choix en utilisant les choix définis dans le modèle CustomUser.UserRole,
            # mais en n'incluant que les rôles souhaités pour l'inscription publique.
            self.fields['role'].choices = [
                (CustomUser.UserRole.STUDENT, CustomUser.UserRole.STUDENT.label),
                (CustomUser.UserRole.INSTRUCTOR, CustomUser.UserRole.INSTRUCTOR.label),
                # N'incluez PAS CustomUser.UserRole.ADMIN ici pour la sécurité
            ]
            # --- Fin limitation des choix ---


    # Optionnel : Vous pouvez override la méthode save si vous avez besoin de logique supplémentaire
    # def save(self, commit=True):
    #     user = super().save(commit=False)
    #     # Le rôle est déjà défini par défaut dans le modèle CustomUser (STUDENT)
    #     # Si vous deviez changer le rôle ici, ce serait avant user.save() si commit=False
    #     if commit:
    #         user.save() # Sauvegarde l'objet user, y compris le fichier photo si présent
    #     return user
    
    
    
# formulaire de creation formateur a partir de creation de session pour une formation:
#-------------------------------------------------------------------------------------
  
class FormateurCreationForm(UserCreationForm):
    """
    Formulaire spécialisé pour créer un formateur (utilisateur avec rôle INSTRUCTOR)
    Hérite de UserCreationForm pour gérer proprement le mot de passe
    """
    class Meta:
        model = CustomUser
        fields = ['username', 'password1', 'password2', 
                 'first_name', 'last_name', 'email', 
                 'telephone', 'adress', 'date_naissance', 'photo', 'role']
        widgets = {
            'date_naissance': forms.DateInput(attrs={'type': 'date'}),
            'adress': forms.Textarea(attrs={'rows': 4}),
            'role': forms.HiddenInput(),  # On cache le champ car il est défini automatiquement
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].initial = UserRole.INSTRUCTOR

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = UserRole.INSTRUCTOR
        if commit:
            user.save()
        return user