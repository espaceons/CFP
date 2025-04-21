# gestion_formations/models.py (Version avec Sessions et Séances)

from django.db import models
from django.utils.translation import gettext_lazy as _
# liaison des sessions et potentiellement les séances à un formateur


class Formation(models.Model):
    """
    Modèle représentant une formation ou un cours.
    """
    nom = models.CharField(max_length=255, verbose_name=_("Nom de la formation"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    duree_heures = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_("Durée totale en heures") # Durée totale estimée de la formation
    )
    objectifs = models.TextField(blank=True, null=True, verbose_name=_("Objectifs"))
    prerequis = models.TextField(blank=True, null=True, verbose_name=_("Prérequis"))
    est_active = models.BooleanField(default=True, verbose_name=_("Est active"))

    class Meta:
        verbose_name = _("Formation")
        verbose_name_plural = _("Formations")

    def __str__(self):
        return self.nom

class Session(models.Model):
    """
    Modèle représentant une instance spécifique (une "cohorte") d'une formation.
    Contient les informations générales de la session (période, formateur principal, capacité).
    """
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name='sessions', verbose_name=_("Formation")) # Si la formation est supprimée, ses sessions le sont aussi
    nom_session = models.CharField(max_length=255, verbose_name=_("Nom de la session")) # Nom spécifique de cette session (ex: "Automne 2025", "Intensif Été")
    date_debut_session = models.DateField(verbose_name=_("Date de début de la session")) # Période générale
    date_fin_session = models.DateField(verbose_name=_("Date de fin de la session"))   # Période générale
    capacite_max = models.PositiveIntegerField(verbose_name=_("Capacité maximale"))

    # Formateur principal de la session (peut être différent par séance)
    instructor_principal = models.ForeignKey( 'gestion_inscriptions.Instructor', on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions_principales', verbose_name=_("Formateur principal") )# Permet d'accéder aux sessions où le formateur est principal ex: instructor.sessions_principales.all()
    # --- ATTENTION : LE CHAMP 'lieu' EST DÉCLARÉ UNE SEULE FOIS ICI ---
    lieu = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Lieu de la session")) # Lieu principal de la session (peut être remplacé par séance) exp : salle01, salle02, etc.
    description = models.TextField(blank=True, null=True, verbose_name=_("Description de la session"))
    capacite_min = models.PositiveIntegerField(blank=True, null=True, verbose_name=_("Capacité minimale"))
    
    # Vous pouvez ajouter d'autres champs spécifiques à la session


    class Meta:
        verbose_name = _("Session")
        verbose_name_plural = _("Sessions")
        ordering = ['date_debut_session'] # Trie par défaut par date de début de session

    def __str__(self):
        return f"{self.nom_session} ({self.formation.nom})"

# Nouveau modèle pour les séances individuelles
class Seance(models.Model):
    """
    Modèle représentant une séance spécifique au sein d'une session.
    """
    session = models.ForeignKey( Session,
        on_delete=models.CASCADE, # Si la session est supprimée, ses séances le sont aussi
        related_name='seances',   # Permet d'accéder aux séances depuis une session (session.seances.all())
        verbose_name=_("Session")
    )
    date = models.DateField(verbose_name=_("Date de la séance"))
    heure_debut = models.TimeField(verbose_name=_("Heure de début"))
    heure_fin = models.TimeField(verbose_name=_("Heure de fin"))

    # Formateur spécifique pour cette séance (optionnel, peut remplacer le formateur principal de la session)
    instructor = models.ForeignKey(
        'gestion_inscriptions.Instructor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='seances_enseignees', # Permet d'accéder aux séances d'un formateur ex: instructor.seances_enseignees.all()
        verbose_name=_("Formateur de la séance")
    )
    # --- ATTENTION : LE CHAMP 'lieu' EXISTE ICI POUR LE LIEU SPÉCIFIQUE ---
    lieu_seance = models.CharField( # Lieu spécifique pour cette séance (peut remplacer le lieu principal de la session si défini)
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Lieu de la séance")
    )

    sujet_aborde = models.CharField(max_length=255, blank=True, null=True)
    est_annulee = models.BooleanField(default=False)
    note_seance = models.TextField(blank=True, null=True, verbose_name=_("Notes de la séance")) # Notes spécifiques à cette séance
    # Vous pouvez ajouter d'autres champs spécifiques à une séance (ex: matériel requis, notes de séance, etc.)

    class Meta:
        verbose_name = _("Séance")
        verbose_name_plural = _("Séances")
        ordering = ['date', 'heure_debut'] # Trie par défaut par date et heure de séance

    def __str__(self):
        return f"Séance du {self.date.strftime('%Y-%m-%d')} ({self.heure_debut.strftime('%H:%M')}-{self.heure_fin.strftime('%H:%M')}) pour {self.session.nom_session}"