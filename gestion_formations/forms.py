# gestion_formations/forms.py

from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError

from gestion_users.models import CustomUser, UserRole
from .models import Formation, Room, Seance, Session
from gestion_inscriptions.models import Instructor
from django.db.models import Q
from django.forms import modelformset_factory
from django.shortcuts import  get_object_or_404

# formulaire de la formation :
#-----------------------------

class FormationForm(forms.ModelForm):
    """
    Formulaire pour créer ou mettre à jour une formation.
    """
    class Meta:
        model = Formation
        fields = '__all__'
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'objectifs': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'prerequis': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'duree_heures': forms.NumberInput(attrs={'class': 'form-control'}),
            'est_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        

# --- Formulaire pour Séance (après modification du modèle Seance) ---
class SeanceForm(forms.ModelForm):
    """
    Formulaire pour créer ou modifier une Séance.
    Maintenant lié au modèle Room par une ForeignKey.
    """
    class Meta:
        model = Seance
        fields = [
            'session',
            'date',
            'heure_debut',
            'heure_fin',
            'room', # Le nouveau champ ForeignKey
            'instructor',
            'sujet_aborde',
            'est_annulee',
            'note_seance',
            # 'created_by', 'updated_at' si ajoutés au modèle mais souvent gérés automatiquement ou en vue
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'heure_debut': forms.TimeInput(attrs={'type': 'time'}),
            'heure_fin': forms.TimeInput(attrs={'type': 'time'}),
            'note_seance': forms.Textarea(attrs={'rows': 3}),
        }

    # --- Fonction helper pour trouver les salles disponibles ---
# Cette fonction est utilisée par le formulaire pour filtrer les choix de salles.
def get_available_rooms_for_seance(session_id, seance_date, seance_heure_debut, seance_heure_fin, current_seance_id=None):
    """
    Retourne un queryset des salles disponibles pour un créneau horaire donné,
    en tenant compte des réservations existantes et de la capacité requise.

    Args:
        session_id (int): L'ID de la session pour connaître la capacité requise.
        seance_date (date): La date de la séance.
        seance_heure_debut (time): L'heure de début de la séance.
        seance_heure_fin (time): L'heure de fin de la séance.
        current_seance_id (int, optional): L'ID de la séance en cours de modification.
                                           Permet d'exclure cette séance de la vérification d'occupation.

    Returns:
        QuerySet: Un queryset des objets Room disponibles.
    """
    # Récupérer la session pour connaître la capacité maximale
    try:
        session = Session.objects.get(pk=session_id)
        capacite_requise = session.capacite_max
    except Session.DoesNotExist:
        # Si la session n'existe pas, on ne peut pas vérifier la capacité requise.
        # On peut choisir de ne retourner aucune salle ou toutes les salles.
        # Retournons un queryset vide pour être prudent.
        print(f"AVERTISSEMENT: Session with ID {session_id} not found when checking room availability.")
        return Room.objects.none()


    # Trouver les séances qui se chevauchent avec le créneau horaire donné à la même date
    # Condition de chevauchement : Début < Fin_Autre ET Fin > Début_Autre
    # Note : Cette logique suppose que heure_fin est toujours après heure_debut le même jour.
    # Si les séances peuvent traverser minuit, la logique de chevauchement doit être plus complexe.
    overlapping_seances = Seance.objects.filter(
        date=seance_date
    ).filter(
        Q(heure_debut__lt=seance_heure_fin) & Q(heure_fin__gt=seance_heure_debut)
    )

    # Si nous modifions une séance existante, l'exclure de la vérification de chevauchement
    if current_seance_id:
         overlapping_seances = overlapping_seances.exclude(pk=current_seance_id)

    # Obtenir les IDs des salles qui sont occupées par ces séances qui se chevauchent
    # On veut les IDs des salles, en s'assurant qu'elles ne sont pas NULL (pour les séances sans salle attribuée)
    booked_room_ids = overlapping_seances.exclude(room__isnull=True).values_list('room', flat=True).distinct()

    # Filtrer les salles disponibles :
    # 1. Elles doivent être assez grandes pour la capacité requise
    # 2. Elles ne doivent PAS être dans la liste des IDs de salles occupées (booked_room_ids)
    available_rooms_queryset = Room.objects.filter(capacity__gte=capacite_requise)

    # Exclure les salles qui sont occupées à ce créneau
    available_rooms_queryset = available_rooms_queryset.exclude(pk__in=booked_room_ids)

    return available_rooms_queryset


# --- Formulaire pour Séance (après modification du modèle Seance) ---
class SeanceForm(forms.ModelForm):
    """
    Formulaire pour créer ou modifier une Séance.
    Maintenant lié au modèle Room par une ForeignKey.
    Le champ 'room' est filtré dynamiquement.
    """
    class Meta:
        model = Seance
        fields = [
            'session',
            'date',
            'heure_debut',
            'heure_fin',
            'room', # Le nouveau champ ForeignKey
            'instructor',
            'sujet_aborde',
            'est_annulee',
            'note_seance',
            # Ajoutez 'created_by' et 'updated_at' ici si vous voulez les afficher/modifier dans le formulaire,
            # mais ils sont souvent gérés automatiquement ou en vue.
            # 'created_by',
            # 'updated_at',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'heure_debut': forms.TimeInput(attrs={'type': 'time'}),
            'heure_fin': forms.TimeInput(attrs={'type': 'time'}),
            'note_seance': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        # --- Gérer l'objet request et session_pk passés aux kwargs ---
        # Récupérer l'objet request si il est passé, et le retirer de kwargs
        self.request = kwargs.pop('request', None)
        # Récupérer la session_pk si elle est passée, et la retirer de kwargs
        session_pk = kwargs.pop('session_pk', None)

        # Appeler la méthode __init__ de la classe parente avec les arguments restants
        super().__init__(*args, **kwargs)

        # --- Pré-filtrage du queryset du champ 'room' ---
        # Ce filtrage est fait lors de l'affichage initial du formulaire (GET)
        # et peut être basé sur l'instance existante (modification) ou la session_pk (création)

        instance = self.instance # L'instance Seance si on est en modification
        seance_date = None
        seance_heure_debut = None
        seance_heure_fin = None
        current_seance_id = None
        session_id = None # Pour passer à la fonction helper

        if instance and instance.pk: # Si on modifie une séance existante
            seance_date = instance.date
            seance_heure_debut = instance.heure_debut
            seance_heure_fin = instance.heure_fin
            current_seance_id = instance.pk
            session_id = instance.session.pk # Récupérer l'ID de la session liée

        elif session_pk: # Si on crée une séance pour une session spécifique (session_pk passé)
             session_id = session_pk
             # En création, la date/heures ne sont pas connues lors de l'initialisation du formulaire.
             # Le filtrage complet basé sur le chevauchement n'est pas possible ici.
             # On peut au moins filtrer par capacité si session_id est connu.
             # Les valeurs initiales pourraient être utilisées si elles sont passées :
             # seance_date = self.initial.get('date')
             # seance_heure_debut = self.initial.get('heure_debut')
             # seance_heure_fin = self.initial.get('heure_fin')


        # Définir le queryset du champ 'room'
        # Si on a les infos de date/heure ET l'ID de session (en modification ou avec initiales complètes),
        # on filtre par disponibilité en utilisant la fonction helper.
        if seance_date and seance_heure_debut and seance_heure_fin and session_id is not None:
            self.fields['room'].queryset = get_available_rooms_for_seance(
                session_id=session_id,
                seance_date=seance_date,
                seance_heure_debut=seance_heure_debut,
                seance_heure_fin=seance_heure_fin,
                current_seance_id=current_seance_id # Passer l'ID de la séance en cours si modification
            )
        elif session_id is not None:
             # En création sans date/heure connues lors de l'initialisation,
             # on peut au moins filtrer par capacité si session_id est connu.
             try:
                 session_obj = Session.objects.get(pk=session_id)
                 self.fields['room'].queryset = Room.objects.filter(capacity__gte=session_obj.capacite_max)
             except Session.DoesNotExist:
                 # Gérer l'erreur si la session n'existe pas (devrait être géré par get_object_or_404 dans la vue)
                 self.fields['room'].queryset = Room.objects.none() # Pas de salles disponibles si la session est invalide
                 # Vous pourriez aussi ajouter un message d'erreur global ici si nécessaire


        # --- Optionnel : Cacher le champ 'session' ---
        # Si le formulaire est utilisé dans un contexte où la session est déjà connue (ex: création/modification depuis page session_detail)
        # on peut cacher le champ 'session' et le pré-remplir.
        if 'session' in self.fields and session_pk is not None:
             self.fields['session'].widget = forms.HiddenInput()
             # Pré-remplir le champ session s'il est caché et session_pk est connu
             # On utilise initial ici, la validation dans clean() s'assurera qu'il est correct
             # self.fields['session'].initial = get_object_or_404(Session, pk=session_pk)
             # Note : Dans la vue CreateView/UpdateView, il est souvent plus simple
             # de définir form.instance.session = session_obj dans form_valid()
             # plutôt que de gérer l'initial ici si le champ est caché.


    # --- Validation personnalisée dans clean() ---
    # Ceci est CRUCIAL pour un formulaire de CRÉATION où date/heure/salle sont entrés par l'utilisateur
    # Et pour un formulaire de MODIFICATION si date/heure/salle sont modifiés
    # Cette méthode est appelée après la validation des champs individuels.
    def clean(self):
        # Appeler la méthode clean de la classe parente pour obtenir les données validées
        cleaned_data = super().clean()

        # Récupérer les données des champs nécessaires à la validation
        seance_date = cleaned_data.get('date')
        seance_heure_debut = cleaned_data.get('heure_debut')
        seance_heure_fin = cleaned_data.get('heure_fin')
        selected_room = cleaned_data.get('room')
        session_obj = cleaned_data.get('session') # Récupérer la session depuis les données nettoyées

        # --- Validation de la plage horaire ---
        if seance_heure_debut and seance_heure_fin and seance_heure_debut >= seance_heure_fin:
             self.add_error('heure_fin', _("L'heure de fin doit être postérieure à l'heure de début."))
             # Retourner cleaned_data ici si vous voulez arrêter la validation après cette erreur
             # return cleaned_data

        # --- Validation de la date par rapport à la période de la session ---
        if seance_date and session_obj:
             if seance_date < session_obj.date_debut_session or seance_date > session_obj.date_fin_session:
                 self.add_error('date', _("La date de la séance doit être comprise dans la période de la session."))
                 # return cleaned_data


        # --- Vérification de la disponibilité de la salle (chevauchement) ---
        # Ne vérifier la disponibilité que si tous les champs nécessaires sont présents et valides
        # (les erreurs précédentes auront peut-être déjà ajouté des erreurs)
        # On vérifie si 'date', 'heure_debut', 'heure_fin', 'room' et 'session' sont dans cleaned_data
        # et ne sont pas None (ce qui peut arriver si un champ individuel n'a pas passé sa validation)
        if all([seance_date, seance_heure_debut, seance_heure_fin, selected_room, session_obj]) and not self.errors:
            # Récupérer l'instance de la séance si elle existe (pour l'exclure de la vérification en modification)
            # self.instance est l'objet Seance si on est en modification, None si on est en création
            current_seance_id = self.instance.pk if self.instance and self.instance.pk else None

            # Utiliser la fonction helper pour trouver les salles disponibles pour ce créneau
            # Si la salle sélectionnée n'est PAS dans le queryset des salles disponibles, c'est qu'elle est occupée.
            available_rooms_at_this_time = get_available_rooms_for_seance(
                session_id=session_obj.pk, # Passer l'ID de la session
                seance_date=seance_date,
                seance_heure_debut=seance_heure_debut,
                seance_heure_fin=seance_heure_fin,
                current_seance_id=current_seance_id # Passer l'ID de la séance en cours (sera None en création)
            )

            # Vérifier si la salle sélectionnée fait partie des salles disponibles calculées
            if selected_room not in available_rooms_at_this_time:
                # Si la salle sélectionnée n'est pas disponible, ajouter une erreur
                self.add_error('room', _("La salle sélectionnée n'est pas disponible à ce créneau horaire ou ne correspond pas à la capacité requise."))
                # Alternative plus spécifique si vous voulez distinguer capacité et chevauchement :
                # if selected_room.capacity < session_obj.capacite_max:
                #      self.add_error('room', _("La salle sélectionnée n'est pas assez grande pour cette session."))
                # else: # Si la capacité est OK, c'est qu'elle est occupée
                #      self.add_error('room', _("Cette salle est déjà réservée à ce créneau horaire."))


        # Retourner les données nettoyées (avec les erreurs ajoutées si nécessaire)
        return cleaned_data



# formulaire de Session:
#-----------------------

class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = [
            'formation',
            'nom_session',
            'statut',
            'date_debut_session',
            'date_fin_session',
            'instructor_principal',
            'lieu',
            'capacite_max',
            'capacite_min',
            'description'
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
        
        # Filtre les formations actives seulement
        self.fields['formation'].queryset = Formation.objects.filter(est_active=True)
        
        # Filtrer les utilisateurs actifs de type formateur
        self.fields['instructor_principal'].queryset = CustomUser.objects.filter(is_active=True, role=UserRole.INSTRUCTOR)

        
        # Si instance existe (mode édition), on adapte les choix
        if self.instance and self.instance.pk:
            self.fields['formation'].disabled = True
            self.initial['capacite_min'] = self.instance.capacite_min or 5

    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut_session')
        date_fin = cleaned_data.get('date_fin_session')
        capacite_max = cleaned_data.get('capacite_max')
        capacite_min = cleaned_data.get('capacite_min', 5)  # Valeur par défaut

        # Validation des dates
        if date_debut and date_fin:
            if date_fin < date_debut:
                self.add_error('date_fin_session', "La date de fin doit être après la date de début.")
            
            # Validation si on modifie une session en cours
            if self.instance and self.instance.pk:
                if self.instance.statut in ['IN_PROGRESS', 'COMPLETED'] and date_debut != self.instance.date_debut_session:
                    self.add_error('date_debut_session', "Impossible de modifier la date de début d'une session en cours ou terminée.")

        # Validation des capacités
        if capacite_max and capacite_min:
            if capacite_min < 1:
                self.add_error('capacite_min', "La capacité minimale doit être d'au moins 1 participant.")
            if capacite_max < capacite_min:
                self.add_error('capacite_max', f"La capacité maximale doit être supérieure ou égale à la capacité minimale ({capacite_min}).")
            elif capacite_max > 100:
                self.add_error('capacite_max', "La capacité maximale ne peut excéder 100 participants.")

        # Validation du formateur principal
        instructor = cleaned_data.get('instructor_principal')
        if instructor and date_debut and date_fin:
            # Vérifie si le formateur a d'autres sessions pendant cette période
            conflits = Session.objects.filter(
                Q(instructor_principal=instructor),
                Q(date_debut_session__lte=date_fin),
                Q(date_fin_session__gte=date_debut)
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if conflits.exists():
                self.add_error('instructor_principal', 
                    f"Ce formateur a déjà une session du {conflits[0].date_debut_session} au {conflits[0].date_fin_session}")

        return cleaned_data
    
    
    
SeanceFormSet = modelformset_factory(
    Seance,
    form=SeanceForm, # Utilise votre SeanceForm personnalisé
    extra=3,         # Afficher 3 formulaires vides par défaut pour l'ajout
    can_delete=False # Nous sommes dans une vue de création, pas besoin de supprimer les existants
    # Si vous adaptez cette vue pour aussi MODIFIER/SUPPRIMER, mettez can_delete=True
) 
