# gestion_users/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

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
    role = models.CharField( max_length=50, choices=UserRole.choices, default=UserRole.STUDENT,  verbose_name=_("Rôle")) # role par défaut est 'Étudiant'
    telephone = models.CharField( max_length=15, blank=True, null=True, verbose_name=_("Téléphone") )
    adress = models.TextField( blank=True, null=True, verbose_name=_("Adresse"))
    date_naissance = models.DateField( blank=True, null=True, verbose_name=_("Date de naissance") )
    
    # Vous devrez vérifier le rôle directement via user.role == UserRole.ADMIN/INSTRUCTOR/STUDENT
    # ou via l'existence des profils Instructor/Student liés.

    class Meta:
        verbose_name = _("Utilisateur")
        verbose_name_plural = _("Utilisateurs")

    def __str__(self):
        # Représentation textuelle de l'utilisateur
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

# Assurez-vous que AUTH_USER_MODEL = 'gestion_users.CustomUser' est toujours dans settings.py
# Si vous avez déjà créé ce modèle et appliqué les migrations,
# retirer des méthodes Python comme celles-ci ne nécessite PAS de nouvelles migrations.