# gestion_formations/forms.py

from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError

from gestion_users.models import CustomUser, UserRole
from .models import Formation, Seance, Session
from gestion_inscriptions.models import Instructor
from django.db.models import Q

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
        
        
# formulaire de Seance:
#----------------------

class SeanceForm(forms.ModelForm):
    class Meta:
        model = Seance
        fields = [
            'session',
            'date',
            'heure_debut',
            'heure_fin',
            'instructor',
            'lieu_seance',
            'sujet_aborde',
            'note_seance',
            'est_annulee'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'heure_debut': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'heure_fin': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'note_seance': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'session': forms.HiddenInput(),  # Caché car défini dans la vue
        }

    def __init__(self, *args, **kwargs):
        session_pk = kwargs.pop('session_pk', None)
        super().__init__(*args, **kwargs)
        
        # Filtre les formateurs disponibles
        self.fields['instructor'].queryset = Instructor.objects.filter(est_actif=True)
        
        # Si on crée une nouvelle séance pour une session spécifique
        if session_pk:
            session = Session.objects.get(pk=session_pk)
            self.fields['session'].initial = session
            self.fields['lieu_seance'].initial = session.lieu
            
            # Si la session a un formateur principal, on le propose par défaut
            if session.instructor_principal:
                self.fields['instructor'].initial = session.instructor_principal

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        heure_debut = cleaned_data.get('heure_debut')
        heure_fin = cleaned_data.get('heure_fin')
        instructor = cleaned_data.get('instructor')
        session = cleaned_data.get('session')

        # Validation de la date par rapport à la session
        if session and date:
            if date < session.date_debut_session:
                self.add_error('date', "La date ne peut pas être avant le début de la session.")
            if date > session.date_fin_session:
                self.add_error('date', "La date ne peut pas être après la fin de la session.")

        # Validation des heures
        if heure_debut and heure_fin:
            if heure_fin <= heure_debut:
                self.add_error('heure_fin', "L'heure de fin doit être après l'heure de début.")
            
            # Vérification des conflits pour le formateur
            if instructor and date:
                conflits = Seance.objects.filter(
                    instructor=instructor,
                    date=date,
                    heure_debut__lt=heure_fin,
                    heure_fin__gt=heure_debut
                ).exclude(pk=self.instance.pk if self.instance else None)
                
                if conflits.exists():
                    self.add_error('instructor', "Ce formateur a déjà une séance à cette plage horaire.")

            # Vérification des conflits pour le lieu
            lieu_seance = cleaned_data.get('lieu_seance')
            if lieu_seance and date:
                conflits = Seance.objects.filter(
                    lieu_seance=lieu_seance,
                    date=date,
                    heure_debut__lt=heure_fin,
                    heure_fin__gt=heure_debut
                ).exclude(pk=self.instance.pk if self.instance else None)
                
                if conflits.exists():
                    self.add_error('lieu_seance', "Ce lieu est déjà occupé à cette plage horaire.")

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
    
    