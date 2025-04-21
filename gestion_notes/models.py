# gestion_notes/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal # Pour le champ DecimalField
from gestion_formations.models import Seance
# Importation de gettext_lazy pour la traduction des chaînes de caractères
# Importe le modèle Enrollment car une note est liée à une inscription
# Utilise la chaîne de caractères pour éviter les dépendances circulaires potentielles
from gestion_inscriptions.models import Enrollment # Importe le modèle Enrollment


class EvaluationType(models.Model):
    """
    Modèle représentant un type d'évaluation (Examen, Projet, etc.).
    """
    nom = models.CharField(max_length=100, unique=True, verbose_name=_("Nom du type d'évaluation"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    # Vous pourriez ajouter un champ pour le poids par défaut de ce type d'évaluation
    # poids_par_defaut = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('1.0'), verbose_name=_("Poids par défaut"))


    class Meta:
        verbose_name = _("Type d'évaluation")
        verbose_name_plural = _("Types d'évaluation")

    def __str__(self):
        return self.nom

class Evaluation(models.Model):
    """
    Modèle représentant une note ou une évaluation spécifique pour un étudiant.
    Lié à une inscription.
    """
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE, # Si l'inscription est supprimée, les évaluations associées le sont aussi
        related_name='evaluations', # Permet d'accéder aux évaluations depuis une inscription exp : Enrollment.evaluations.all()
        verbose_name=_("Inscription")
    )
    evaluation_type = models.ForeignKey(
        EvaluationType,
        on_delete=models.PROTECT, # Empêche la suppression d'un type d'évaluation s'il est utilisé
        related_name='evaluations', # Permet d'accéder aux évaluations d'un type
        verbose_name=_("Type d'évaluation")
    )
    # pour pouvoir calculer des moyennes pondérées par la suite.
    poids_evaluation = models.DecimalField(
        max_digits=5,       # Nombre total de chiffres (ex: 100.00, 20.00)
        decimal_places=2,
        verbose_name=_("Poids de l'évaluation")
    )
    note = models.DecimalField(
        max_digits=5,       # Nombre total de chiffres (ex: 100.00, 20.00)
        decimal_places=2,   # Nombre de chiffres après la virgule
        verbose_name=_("Note")
    )

    # Vous pouvez lier l'évaluation à une séance spécifique si la note est donnée lors d'un cours, ex: un quiz de fin de cours
    
    seance = models.ForeignKey(
        'gestion_formations.Seance', # Utilise la chaîne de caractères
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='evaluations', # Permet d'accéder aux évaluations d'une séance exp : seance.evaluations.all()
        verbose_name=_("Séance associée") # Séance à laquelle la note est liée (si applicable) exp : seance.nom_seance
    )
    
    
    # Formateur qui a donné la note (si applicable)
    instructor = models.ForeignKey(
        'gestion_users.CustomUser', # Utilise la chaîne de caractères pour éviter les dépendances circulaires
        limit_choices_to={'role': 'INSTRUCTOR'}, # Limite les choix aux formateurs uniquement
        on_delete=models.PROTECT,
        related_name='evaluations_given', # Permet d'accéder aux évaluations données par un formateur exp : instructor.evaluations_given.all()
        verbose_name=_("Formateur") # Formateur qui a donné la note (si applicable) exp : instructor.get_full_name()
    )

    date_evaluation = models.DateField( blank=True, null=True, verbose_name=_("Date de l'évaluation") ) # Date à laquelle l'évaluation a été donnée
    commentaires = models.TextField( blank=True, null=True, verbose_name=_("Commentaires") ) # Commentaires sur l'évaluation
    # Vous pourriez ajouter d'autres champs si nécessaire (ex: poids de l'évaluation, date limite, etc.)


    class Meta:
        verbose_name = _("Évaluation")
        verbose_name_plural = _("Évaluations")
        # Optionnel mais utile : assure qu'un étudiant n'a qu'une note pour un type d'évaluation donné DANS une session
        # Cela nécessiterait un unique_together avec enrollment et evaluation_type
        # unique_together = ('enrollment', 'evaluation_type')


    def __str__(self):
        # Affiche l'étudiant, le type d'évaluation et la note
        return f"Note de {self.note} pour {self.enrollment.student} ({self.evaluation_type.nom} - {self.enrollment.session.nom_session})"