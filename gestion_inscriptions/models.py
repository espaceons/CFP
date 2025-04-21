# gestion_inscriptions/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
# Importe le modèle utilisateur personnalisé depuis gestion_users
# Assurez-vous que 'gestion_users' est bien le nom de l'app
# et 'CustomUser' le nom du modèle que vous avez défini
from gestion_users.models import CustomUser
from gestion_formations.models import Session, Seance # importation des model Session et Seance

class Instructor(models.Model):
    """
    Modèle de profil spécifique pour les formateurs.
    Contient les informations supplémentaires propres aux formateurs.
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE, # Si l'utilisateur est supprimé, le profil  formateur supprimé
        primary_key=True,         # Utilise le user_id comme clé primaire pour simplifier
        related_name='instructor', # Permet d'accéder au profil formateur depuis l'utilisateur (user.instructor)
        verbose_name=_("Utilisateur")
    )
    specialite_enseignement = models.CharField(
        max_length=255,
        blank=True, # Le champ peut être vide
        null=True,  # Permet NULL dans la base de données
        verbose_name=_("Spécialité d'enseignement")
    )
    # Vous pouvez ajouter d'autres champs spécifiques au formateur ici
    # Exemple : bio = models.TextField(blank=True, null=True, verbose_name=_("Biographie"))
    # coordonnees_contact = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Coordonnées de contact (pour le centre)"))


    class Meta:
        verbose_name = _("Formateur")
        verbose_name_plural = _("Formateurs")

    def __str__(self):
        # Affiche le nom de l'utilisateur lié pour identifier le formateur
        return f"Formateur: {self.user.get_full_name() or self.user.username}"

# On peut aussi créer un modèle Student ici, lié à l'utilisateur
class Student(models.Model):
    """
    Modèle de profil spécifique pour les étudiants.
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE, # Si l'utilisateur est supprimé, le profil étudiant supprimé
        primary_key=True,
        related_name='student', # Permet d'accéder au profil étudiant depuis l'utilisateur (user.student)
        verbose_name=_("Utilisateur")
    )
    numero_etudiant = models.CharField(
        max_length=50,
        unique=True, # Chaque étudiant a un numéro unique
        blank=True,
        null=True,
        verbose_name=_("Numéro Étudiant")
    )
    # Ajoutez d'autres champs spécifiques à l'étudiant ici (ex: niveau d'études, adresse, tuteur, etc.)


    class Meta:
        verbose_name = _("Étudiant")
        verbose_name_plural = _("Étudiants")

    def __str__(self):
        # Affiche le numéro étudiant ou le nom de l'utilisateur
        return f"Étudiant: {self.numero_etudiant or self.user.get_full_name() or self.user.username}"



# ---  Modèles pour l'Inscription et la Présence ---
#--------------------------------------------------------------

# Ces modèles sont liés à la gestion des inscriptions (Enrollment) et de la présence (Attendance) des étudiants dans les sessions et séances.

class EnrollmentStatus(models.TextChoices):
    PENDING = 'PENDING', _('En attente') # En attente d'approbation
    APPROVED = 'APPROVED', _('Approuvée') # Inscription approuvée par l'administration
    REJECTED = 'REJECTED', _('Rejetée') # Inscription rejetée par l'administration
    CANCELLED = 'CANCELLED', _('Annulée') # Annulée par l'étudiant ou l'administration

class Enrollment(models.Model):
    """
    Modèle représentant l'inscription d'un étudiant à une session.
    """
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE, # Si l'étudiant est supprimé, son inscription est supprimée
        related_name='enrollments', # Permet d'accéder aux inscriptions d'un étudiant exp : student.enrollments.all()
        verbose_name=_("Étudiant") # Utilise le modèle Student pour représenter l'étudiant
    )
    session = models.ForeignKey(
        'gestion_formations.Session', # En utilisant les chaînes de caractères pour les références entre ces deux applications, vous cassez la dépendance circulaire et Django pourra charger vos modèles correctement.
        on_delete=models.CASCADE, # Si la session est supprimée, ses inscriptions sont supprimées
        related_name='enrollments', # Permet d'accéder aux inscriptions d'une session exp : session.enrollments.all()
        verbose_name=_("Session") # Utilise le modèle Session pour représenter la session exp : session.nom_session
    )
    date_inscription = models.DateField(auto_now_add=True, verbose_name=_("Date d'inscription")) # Date automatique de création de l'inscription
    statut = models.CharField(
        max_length=50,
        choices=EnrollmentStatus.choices,
        default=EnrollmentStatus.PENDING,
        verbose_name=_("Statut de l'inscription")
    )
    date_statut = models.DateField(blank=True, null=True, verbose_name=_("Date de changement de statut")) # Date à laquelle le statut a été modifié

    # Vous pouvez ajouter d'autres champs si nécessaire (ex: date_statut, notes_admin, etc.)

    class Meta:
        verbose_name = _("Inscription")
        verbose_name_plural = _("Inscriptions")
        # Empêche un étudiant de s'inscrire deux fois à la même session
        unique_together = ('student', 'session')

    def __str__(self):
        return f"Inscription de {self.student} à {self.session}"

class AttendanceStatus(models.TextChoices):
    PRESENT = 'PRESENT', _('Présent') # Présent à la séance
    ABSENT = 'ABSENT', _('Absent') # Absent à la séance
    UNEXCUSED = 'UNEXCUSED', _('Non excusé') # Non excusé pour l'absence
    EXCUSED = 'EXCUSED', _('Excusé') # Excusé pour l'absence
    LATE = 'LATE', _('En retard') # En retard à la séance

    # Ajoutez d'autres statuts si nécessaire

class Attendance(models.Model):
    """
    Modèle représentant la présence d'un étudiant à une séance spécifique.
    Lié à l'inscription pour s'assurer que l'étudiant est bien inscrit à la session de la séance.
    """
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE, # Si l'inscription est supprimée, les enregistrements de présence associés le sont aussi
        related_name='attendances', # Permet d'accéder aux présences depuis une inscription exp : Enrollment.attendances.all()
        verbose_name=_("Inscription") # Inscription à la séance exp 
    )
    seance = models.ForeignKey(
        'gestion_formations.Seance',
        on_delete=models.CASCADE, # Si la séance est supprimée, ses enregistrements de présence le sont aussi
        related_name='attendances', # Permet d'accéder aux présences d'une séance
        verbose_name=_("Séance")
    )
    status = models.CharField(
        max_length=50,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.ABSENT, # Par défaut, on considère l'étudiant comme absent s'il n'est pas marqué
        verbose_name=_("Statut de présence")
    )
    date_enregistrement = models.DateTimeField(auto_now_add=True, verbose_name=_("Date d'enregistrement")) # Quand la présence a été enregistrée

    # Optionnel : Pourrait ajouter un champ 'enregistre_par' lié à CustomUser pour savoir qui a marqué la présence

    class Meta:
        verbose_name = _("Présence")
        verbose_name_plural = _("Présences")
        # Assure qu'il n'y a qu'un seul enregistrement de présence par inscription et par séance
        unique_together = ('enrollment', 'seance')

    def __str__(self):
        # Permet d'afficher "Présence de [Étudiant] à [Séance]"
        return f"Présence de {self.enrollment.student} à {self.seance}"

    # Ajout d'une propriété pour faciliter l'accès à l'étudiant directement depuis l'objet Attendance
    @property
    def student(self):
        return self.enrollment.student

    # Ajout d'une propriété pour faciliter l'accès à la session directement depuis l'objet Attendance
    @property
    def session(self):
        return self.enrollment.session
