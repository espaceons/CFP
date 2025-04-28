# gestion_formations/models.py (Version avec Sessions et Séances)

from django.db import models
from django.utils.translation import gettext_lazy as _

from django.core.exceptions import ValidationError

from datetime import datetime, time

from gestion_users.models import CustomUser
# liaison des sessions et potentiellement les séances à un formateur


class Formation(models.Model): # cours
    """
    Modèle représentant une formation ou un cours.
    """
    nom = models.CharField(max_length=255, verbose_name=_("Nom de la formation"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    duree_heures = models.PositiveIntegerField( blank=True, null=True, verbose_name=_("Durée totale en heures") ) # Durée totale estimée de la formation
    objectifs = models.TextField(blank=True, null=True, verbose_name=_("Objectifs"))
    prerequis = models.TextField(blank=True, null=True, verbose_name=_("Prérequis"))
    est_active = models.BooleanField(default=True, verbose_name=_("Est active"))

    class Meta:
        verbose_name = _("Formation")
        verbose_name_plural = _("Formations")

    def __str__(self):
        return self.nom


class SessionStatus(models.TextChoices):
    PLANNED = 'PLANNED', _('Planifiée')
    OPEN = 'OPEN', _('Ouverte aux inscriptions')
    IN_PROGRESS = 'IN_PROGRESS', _('En cours')
    COMPLETED = 'COMPLETED', _('Terminée')
    CANCELLED = 'CANCELLED', _('Annulée')
    
    
class Session(models.Model):
    """
    Modèle représentant une instance spécifique (une "cohorte") d'une formation.
    Contient les informations générales de la session (période, formateur principal, capacité).
    """
    
    statut = models.CharField( max_length=50, choices=SessionStatus.choices, default=SessionStatus.PLANNED, verbose_name=_("Statut de la session"))
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name='sessions', verbose_name=_("Formation")) # Si la formation est supprimée, ses sessions le sont aussi
    nom_session = models.CharField(max_length=255, verbose_name=_("Nom de la session")) # Nom spécifique de cette session (ex: "Automne 2025", "Intensif Été")
    date_debut_session = models.DateField(verbose_name=_("Date de début de la session")) # Période générale
    date_fin_session = models.DateField(verbose_name=_("Date de fin de la session"))   # Période générale
    capacite_max = models.PositiveIntegerField(verbose_name=_("Capacité maximale"))

    # Formateur principal de la session (peut être différent par séance)
    
    # Permet d'accéder aux sessions où le formateur est principal ex: instructor.sessions_principales.all()
    instructor_principal = models.ForeignKey( CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions_principales', verbose_name=_("Formateur principal") )
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
    Version améliorée avec :
    - Validation des données
    - Historique et traçabilité
    - Méthodes utilitaires
    - Gestion des conflits
    """
    session = models.ForeignKey(
        'Session',
        on_delete=models.CASCADE,
        related_name='seances',
        verbose_name=_("Session")
    )
    date = models.DateField(verbose_name=_("Date de la séance"))
    heure_debut = models.TimeField(verbose_name=_("Heure de début"))
    heure_fin = models.TimeField(verbose_name=_("Heure de fin"))

    instructor = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='seances_enseignees',
        verbose_name=_("Formateur de la séance")
    )
    
    lieu_seance = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Lieu de la séance")
    )

    sujet_aborde = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        verbose_name=_("Sujet abordé")
    )
    
    est_annulee = models.BooleanField(
        default=False,
        verbose_name=_("Séance annulée")
    )
    
    note_seance = models.TextField(
        blank=True, 
        null=True, 
        verbose_name=_("Notes de la séance")
    )
    
    # Nouveaux champs pour la traçabilité
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Dernière modification")
    )
    
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Créé par"),
        related_name='seances_crees'
    )

    class Meta:
        verbose_name = _("Séance")
        verbose_name_plural = _("Séances")
        ordering = ['date', 'heure_debut']
        constraints = [
            models.UniqueConstraint(
                fields=['session', 'date', 'heure_debut'],
                name='unique_seance_time_per_session'
            ),
            models.CheckConstraint(
                check=models.Q(heure_fin__gt=models.F('heure_debut')),
                name='heure_fin_apres_debut'
            )
        ]

    def __str__(self):
        status = " (Annulée)" if self.est_annulee else ""
        return f"{_('Séance du')} {self.date.strftime('%d/%m/%Y')} ({self.heure_debut.strftime('%H:%M')}-{self.heure_fin.strftime('%H:%M')}) - {self.session.nom_session}{status}"

    def clean(self):
        """Validation avancée des données"""
        super().clean()
        
        # Validation des heures
        if self.heure_debut and self.heure_fin:
            if self.heure_fin <= self.heure_debut:
                raise ValidationError({
                    'heure_fin': _("L'heure de fin doit être après l'heure de début.")
                })
            
            # Vérification des plages horaires raisonnables
            if self.heure_debut < time(8, 0) or self.heure_fin > time(20, 0):
                raise ValidationError(
                    _("Les séances doivent être programmées entre 8h et 20h.")
                )

        # Validation des dates par rapport à la session parente
        if hasattr(self, 'session'):
            if self.date < self.session.date_debut_session:
                raise ValidationError({
                    'date': _("La date de la séance ne peut pas être avant le début de la session.")
                })
            if self.date > self.session.date_fin_session:
                raise ValidationError({
                    'date': _("La date de la séance ne peut pas être après la fin de la session.")
                })

    def save(self, *args, **kwargs):
        """Override save pour ajouter la validation"""
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def duree(self):
        """Calcule la durée de la séance en heures"""
        if not all([self.heure_debut, self.heure_fin]):
            return 0
            
        debut = datetime.combine(self.date, self.heure_debut)
        fin = datetime.combine(self.date, self.heure_fin)
        delta = fin - debut
        return delta.total_seconds() / 3600  # Convertit en heures

    @property
    def lieu_effectif(self):
        """Retourne le lieu spécifique ou celui de la session"""
        return self.lieu_seance or self.session.lieu

    @property
    def formateur_effectif(self):
        """Retourne le formateur spécifique ou celui de la session"""
        return self.instructor or self.session.instructor_principal

    def check_conflits(self):
        """
        Vérifie les conflits potentiels avec d'autres séances
        Retourne un dictionnaire avec les conflits trouvés
        """
        conflits = {
            'instructor': None,
            'lieu': None
        }
        
        if not self.date or not self.heure_debut or not self.heure_fin:
            return conflits
            
        # Conflit de formateur
        if self.instructor:
            conflit_formateur = Seance.objects.filter(
                instructor=self.instructor,
                date=self.date,
                heure_debut__lt=self.heure_fin,
                heure_fin__gt=self.heure_debut
            ).exclude(pk=self.pk if self.pk else None)
            
            if conflit_formateur.exists():
                conflits['instructor'] = conflit_formateur.first()

        # Conflit de lieu
        if self.lieu_seance:
            conflit_lieu = Seance.objects.filter(
                lieu_seance=self.lieu_seance,
                date=self.date,
                heure_debut__lt=self.heure_fin,
                heure_fin__gt=self.heure_debut
            ).exclude(pk=self.pk if self.pk else None)
            
            if conflit_lieu.exists():
                conflits['lieu'] = conflit_lieu.first()

        return conflits