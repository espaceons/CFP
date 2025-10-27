# gestion_formations/forms.py

from django import forms
# Import de gettext_lazy pour les messages d'erreur
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms import inlineformset_factory, modelformset_factory
from django.shortcuts import get_object_or_404

# Assurez-vous que tous les modèles sont bien importés
from gestion_users.models import CustomUser, UserRole
from .models import Formation, Room, Seance, Session
# from gestion_inscriptions.models import Instructor # Si Instructor est un modèle séparé, assurez-vous de son utilité


# --- Fonction utilitaire pour trouver les salles disponibles (DOIT être définie AVANT SeanceForm) ---
def get_available_rooms_for_seance(session_id, seance_date, seance_heure_debut, seance_heure_fin, current_seance_id=None):
    """
    Retourne un queryset des salles disponibles pour un créneau horaire donné,
    en tenant compte des réservations existantes, de la capacité requise et des indisponibilités.
    """
    try:
        session = Session.objects.get(pk=session_id)
        capacite_requise = session.capacite_max
    except Session.DoesNotExist:
        # La session n'existe pas, aucune salle n'est possible
        return Room.objects.none()

    # 1. Trouver les séances qui se chevauchent à la même date
    # Condition de chevauchement : Début < Fin_Autre ET Fin > Début_Autre
    overlapping_seances = Seance.objects.filter(
        date=seance_date
    ).filter(
        Q(heure_debut__lt=seance_heure_fin) & Q(
            heure_fin__gt=seance_heure_debut)
    )

    # Exclure la séance en cours de modification
    if current_seance_id:
        overlapping_seances = overlapping_seances.exclude(pk=current_seance_id)

    # Obtenir les IDs des salles occupées par chevauchement
    booked_room_ids = overlapping_seances.exclude(
        room__isnull=True
    ).values_list('room', flat=True).distinct()

    # 2. Trouver les IDs des salles en indisponibilité administrative
    # NOTE: Cette logique dépend du modèle IndisponibiliteSalle dans models.py
    unavailable_room_ids = Room.objects.filter(
        indisponibilites__date_debut__lte=seance_date,  # Début <= date de la séance
        indisponibilites__date_fin__gte=seance_date      # Fin >= date de la séance
    ).values_list('pk', flat=True).distinct()

    # 3. Filtrer les salles disponibles
    available_rooms_queryset = Room.objects.filter(
        capacite__gte=capacite_requise  # Filtre par capacité
    ).exclude(
        pk__in=booked_room_ids  # Exclure les salles occupées par chevauchement
    ).exclude(
        pk__in=unavailable_room_ids  # Exclure les salles en indisponibilité
    )

    return available_rooms_queryset


# --- Formulaire de la formation ---
class FormationForm(forms.ModelForm):
    """Formulaire pour créer ou mettre à jour une formation."""
    class Meta:
        model = Formation
        fields = '__all__'
        # ... (widgets restent identiques) ...
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'objectifs': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'prerequis': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'duree_heures': forms.NumberInput(attrs={'class': 'form-control'}),
            'est_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# --- Formulaire pour Séance ---
class SeanceForm(forms.ModelForm):
    """Formulaire pour créer ou modifier une Séance avec filtrage dynamique de la salle."""
    class Meta:
        model = Seance
        fields = [
            'session',
            'date',
            'heure_debut',
            'heure_fin',
            'room',
            'instructor',
            'sujet_aborde',
            'est_annulee',
            'note_seance',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'heure_debut': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'heure_fin': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'room': forms.Select(attrs={'class': 'form-select'}),
            'instructor': forms.Select(attrs={'class': 'form-select'}),
            'sujet_aborde': forms.TextInput(attrs={'class': 'form-control'}),
            'note_seance': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'est_annulee': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'room': _("Salle de la séance"),
            'sujet_aborde': _("Sujet abordé"),
        }

    def __init__(self, *args, **kwargs):
        # 1. Gérer les kwargs personnalisés (session_pk)
        session_pk = kwargs.pop('session_pk', None)
        kwargs.pop('request', None)

        # 2. Appel de la méthode parente
        super().__init__(*args, **kwargs)

        session_id = self.instance.session_id if self.instance and self.instance.session_id else session_pk
        current_seance_id = self.instance.pk if self.instance else None

        # 🛑 RETRAIT DE LA LOGIQUE HIDDENINPUT ET INITIALISATION FORCÉE 🛑
        # On laisse le champ 'session' se comporter comme un champ normal.
        # Cependant, en mode création, il peut être utile de pré-sélectionner la session :
        if session_pk is not None and 'session' in self.fields:
            # Initialisation pour pré-sélectionner la bonne session dans le Select
            if self.instance._state.adding and session_pk is not None:
                self.initial['session'] = session_pk
            # On ne masque plus le champ ici :
            # self.fields['session'].widget = forms.HiddenInput()

            # 🛑 CORRECTION CRITIQUE (1/2)
            # Initialiser le champ masqué pour garantir que la valeur est dans les données POST
            if self.instance._state.adding:  # Si on est en mode création
                self.initial['session'] = session_id

        # 4. Pré-filtrage du queryset 'room' (par capacité et disponibilité)
        if session_id is not None:
            try:
                # Assurez-vous d'utiliser le bon modèle
                session_obj = Session.objects.get(pk=session_id)

                # Récupérer les valeurs initiales pour le filtrage
                seance_date = self.initial.get('date') or (
                    self.instance.date if self.instance else None)
                seance_heure_debut = self.initial.get('heure_debut') or (
                    self.instance.heure_debut if self.instance else None)
                seance_heure_fin = self.initial.get('heure_fin') or (
                    self.instance.heure_fin if self.instance else None)

                # Si on a les informations de créneau, on filtre par disponibilité complète (mode modification ou retour d'erreur)
                if seance_date and seance_heure_debut and seance_heure_fin:
                    # 🛑 CORRECTION (2/2) :
                    # Cette fonction DOIT utiliser 'capacite__gte' et non 'capacity__gte'
                    room_queryset = get_available_rooms_for_seance(
                        session_id=session_id,
                        seance_date=seance_date,
                        seance_heure_debut=seance_heure_debut,
                        seance_heure_fin=seance_heure_fin,
                        current_seance_id=current_seance_id
                    ).order_by('name')  # Ajout du tri pour un affichage propre
                else:
                    # En mode création SANS données initiales (premier affichage), on filtre uniquement par capacité
                    room_queryset = Room.objects.filter(
                        # Le nom du champ de Room est 'capacite'
                        # Le nom du champ de Session est 'capacite_max' (selon votre code)
                        capacite__gte=session_obj.capacite_max
                    ).order_by('name')

                self.fields['room'].queryset = room_queryset

            except Session.DoesNotExist:
                self.fields['room'].queryset = Room.objects.none()

    def clean(self):
        cleaned_data = super().clean()

        # Récupérer les données nettoyées
        seance_date = cleaned_data.get('date')
        seance_heure_debut = cleaned_data.get('heure_debut')
        seance_heure_fin = cleaned_data.get('heure_fin')
        selected_room = cleaned_data.get('room')

        # Le champ 'session' est maintenant visible
        session_obj = cleaned_data.get('session')
        instructor = cleaned_data.get('instructor')

        # Si le champ 'session' est masqué et n'a pas été posté (erreur de template ou vue), il sera None ici.
        # Si session_obj est None, on ne peut pas faire les validations basées sur la session.
        if session_obj is None and self.instance and self.instance.pk:
            # Tenter de récupérer depuis l'instance en modification
            session_obj = self.instance.session

        # 1. Validation de la plage horaire
        if seance_heure_debut and seance_heure_fin and seance_heure_debut >= seance_heure_fin:
            self.add_error('heure_fin', _(
                "L'heure de fin doit être postérieure à l'heure de début."))

        # 2. Validation de la date par rapport à la période de la session
        if seance_date and session_obj:
            # Le champ de la session dans l'instance du modèle
            date_debut_session = session_obj.date_debut_session
            date_fin_session = session_obj.date_fin_session
            # Vérifiez que les dates de la session ne sont pas None (bien que moins probable si Session est valide)
            if date_debut_session and date_fin_session:
                # Validation des dates par rapport à la session parente
                if seance_date < date_debut_session:
                    raise ValidationError({
                        'date': _("La date de la séance ne peut pas être avant le début de la session (%(date_debut)s).") %
                        {'date_debut': date_debut_session}
                    })
                if seance_date > date_fin_session:
                    raise ValidationError({
                        'date': _("La date de la séance ne peut pas être après la fin de la session (%(date_fin)s).") %
                        {'date_fin': date_fin_session}
                    })
            return cleaned_data

        # 3. Vérification de la disponibilité de la salle (chevauchement et capacité)
        is_valid_time = all(
            [seance_date, seance_heure_debut, seance_heure_fin])

        if is_valid_time and selected_room and session_obj and not self.errors:
            current_seance_id = self.instance.pk if self.instance and self.instance.pk else None

            available_rooms_at_this_time = get_available_rooms_for_seance(
                session_id=session_obj.pk,
                seance_date=seance_date,
                seance_heure_debut=seance_heure_debut,
                seance_heure_fin=seance_heure_fin,
                current_seance_id=current_seance_id
            )

            # Vérifier si la salle sélectionnée est toujours disponible
            if selected_room not in available_rooms_at_this_time:
                # Ajout d'une erreur plus spécifique si possible (capacité vs. chevauchement)
                if selected_room.capacite < session_obj.capacite_max:
                    self.add_error('room', _(
                        f"La salle est trop petite (Capacité requise : {session_obj.capacite_max})."))
                else:
                    self.add_error('room', _(
                        "Cette salle est déjà réservée ou indisponible à ce créneau horaire."))

        # 4. Validation de la disponibilité de l'instructeur (similaire à la salle)
        if instructor and is_valid_time and not self.errors:
            current_seance_id = self.instance.pk if self.instance and self.instance.pk else None

            # Vérifier les chevauchements pour l'instructeur sur d'autres séances
            conflicting_seances = Seance.objects.filter(
                instructor=instructor,
                date=seance_date
            ).filter(
                Q(heure_debut__lt=seance_heure_fin) & Q(
                    heure_fin__gt=seance_heure_debut)
            ).exclude(
                pk=current_seance_id
            )

            if conflicting_seances.exists():
                self.add_error('instructor', _(
                    "Cet instructeur a déjà une séance planifiée à ce créneau horaire."))

        return cleaned_data


class SessionForm(forms.ModelForm):
    # ... (Meta et init) ...
    class Meta:
        model = Session
        fields = [
            'formation', 'nom_session', 'statut', 'date_debut_session', 'date_fin_session',
            'instructor_principal', 'lieu', 'capacite_max', 'capacite_min', 'description'
        ]
        widgets = {
            'date_debut_session': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_fin_session': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'nom_session': "Nom de la session",
            'instructor_principal': "Formateur principal",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['formation'].queryset = Formation.objects.filter(
            est_active=True)
        self.fields['instructor_principal'].queryset = CustomUser.objects.filter(
            is_active=True, role=UserRole.INSTRUCTOR)
        if self.instance and self.instance.pk:
            self.fields['formation'].disabled = True
            self.initial['capacite_min'] = self.instance.capacite_min or 5

    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut_session')
        date_fin = cleaned_data.get('date_fin_session')
        capacite_max = cleaned_data.get('capacite_max')
        capacite_min = cleaned_data.get('capacite_min', 5)

        if date_debut and date_fin:
            if date_fin < date_debut:
                self.add_error(
                    'date_fin_session', "La date de fin doit être après la date de début.")
            if self.instance and self.instance.pk:
                if self.instance.statut in ['IN_PROGRESS', 'COMPLETED'] and date_debut != self.instance.date_debut_session:
                    self.add_error(
                        'date_debut_session', "Impossible de modifier la date de début d'une session en cours ou terminée.")

        if capacite_max and capacite_min:
            if capacite_min < 1:
                self.add_error(
                    'capacite_min', "La capacité minimale doit être d'au moins 1 participant.")
            if capacite_max < capacite_min:
                self.add_error(
                    'capacite_max', f"La capacité maximale doit être supérieure ou égale à la capacité minimale ({capacite_min}).")
            elif capacite_max > 100:
                self.add_error(
                    'capacite_max', "La capacité maximale ne peut excéder 100 participants.")

        instructor = cleaned_data.get('instructor_principal')
        if instructor and date_debut and date_fin:
            conflits = Session.objects.filter(
                Q(instructor_principal=instructor),
                Q(date_debut_session__lte=date_fin),
                Q(date_fin_session__gte=date_debut)
            ).exclude(pk=self.instance.pk if self.instance else None)

            if conflits.exists():
                self.add_error(
                    'instructor_principal', f"Ce formateur a déjà une session du {conflits[0].date_debut_session} au {conflits[0].date_fin_session}")

        return cleaned_data


# Utilisation de inlineformset_factory pour les séances liées à une session
SeanceFormSet = inlineformset_factory(
    Session,
    Seance,
    form=SeanceForm,
    extra=5,
    fields=['date', 'heure_debut', 'heure_fin',
            'instructor', 'room', 'sujet_aborde']
)


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        # Remplacez par les vrais noms de champs de votre modèle Room
        fields = ['name', 'capacite', 'equipements', 'localisation']
