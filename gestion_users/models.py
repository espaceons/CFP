# gestion_users/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _



# Optionnel : Fonction pour déterminer le chemin d'upload de l'image de profil
def user_directory_path(instance, filename):
    # Le fichier sera uploadé dans MEDIA_ROOT/user_<id>/<filename>
    # Assurez-vous que MEDIA_ROOT est configuré dans settings.py
    return f'photos_profil/user_{instance.id}/{filename}' # Chemin d'upload


# On définit toujours les choix pour les rôles
class UserRole(models.TextChoices):
    ADMIN = 'ADMIN', _('Admin')
    INSTRUCTOR = 'INSTRUCTOR', _('Formateur')
    STUDENT = 'STUDENT', _('Étudiant')
    # Vous pouvez ajouter d'autres rôles si nécessaire

class CustomUser(AbstractUser):
    """
    Modèle utilisateur personnalisé avec le champ 'role'.
    Les propriétés de vérification de rôle ont été retirées.
    """
    # Exemple : Ajouter un champ 'role'
    # On définit un rôle par défaut, mais l'admin peut le changer
    
    role = models.CharField( max_length=50, choices=UserRole.choices, default=UserRole.STUDENT,  verbose_name=_("Rôle")) # role par défaut est 'Étudiant'
    
    # Vous pouvez ajouter d'autres champs communs ici si nécessaire,
    # par exemple : telephone = models.CharField(max_length=20, blank=True, null=True)
    # identifiant_centre = models.CharField(max_length=100, unique=True, blank=True, null=True)
    
    telephone = models.CharField( max_length=15, blank=True, null=True, verbose_name=_("Téléphone") )
    adress = models.TextField( blank=True, null=True, verbose_name=_("Adresse"))
    date_naissance = models.DateField( blank=True, null=True, verbose_name=_("Date de naissance") )
    
    photo = models.ImageField(upload_to=user_directory_path, blank=True, null=True, verbose_name=_("Photo de profil"))
    
    # Vous devrez vérifier le rôle directement via user.role == UserRole.ADMIN/INSTRUCTOR/STUDENT
    # ou via l'existence des profils Instructor/Student liés.


    # Champs liés aux permissions spécifiques basées sur le rôle (optionnel)
    # Par défaut, AbstractUser a déjà is_staff, is_superuser.
    # On peut ajouter des propriétés pour vérifier le rôle plus facilement
    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN

    @property
    def is_instructor(self):
        return self.role == UserRole.INSTRUCTOR

    @property
    def is_student(self):
        return self.role == UserRole.STUDENT
    
    
    class Meta:
        verbose_name = _("Utilisateur")
        verbose_name_plural = _("Utilisateurs")
        # Vous pouvez ajouter des contraintes ou index si nécessaire

    def __str__(self):
        # Représentation textuelle de l'utilisateur
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

# Assurez-vous que AUTH_USER_MODEL = 'gestion_users.CustomUser' est toujours dans settings.py
# Si vous avez déjà créé ce modèle et appliqué les migrations,
# retirer des méthodes Python comme celles-ci ne nécessite PAS de nouvelles migrations.



