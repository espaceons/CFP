# gestion_formations/views.py


from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import redirect, render, get_object_or_404 # get_object_or_404 est utile pour les vues basées sur des fonctions
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, TemplateView, ListView
from django.utils import timezone
from datetime import timedelta, time, datetime
from django.db import transaction




from django.contrib.auth.decorators import user_passes_test # Importer user_passes_test



from .models import Formation, Room, Seance, Session # Importe Formation et Session
from .forms import FormationForm, SeanceForm, SeanceFormSet, SessionForm
from django.contrib import messages
from django.db.models import Q

from django.views.generic import CreateView, UpdateView, DeleteView

from django.contrib.auth.mixins import LoginRequiredMixin

from django.core.paginator import Paginator

from django.views import View
from datetime import date
from django.http import JsonResponse


import csv
from django.http import HttpResponse

from django.contrib.auth.decorators import login_required, permission_required



# Formation :
#------------

# listes des formation:
#----------------------

def formation_list(request):
    """
    Vue pour afficher la liste de toutes les formations actives.
    """
    # Récupère tous les objets Formation qui sont actifs depuis la base de données
    formations = Formation.objects.filter(est_active=True)
    
    # fonctionnalité de recherche:
    #-----------------------------
    search_query = request.GET.get('search', '')
    if search_query:
        formations = formations.filter(
            Q(nom__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(objectifs__icontains=search_query)
        )
    # Pagination
    paginator = Paginator(formations, 6)  # 6 formations par page
    page_number = request.GET.get('page')
    formations_page = paginator.get_page(page_number)
        

    context = {
        'formations': formations_page,
        'titre_page': 'Liste des formations disponibles', # Un titre pour la page
        'search_query': search_query,
    }

    return render(request, 'gestion_formations/formation_list.html', context)

# formation inactive liste:
#--------------------------

def formation_inactive_list(request):
    """
    Vue pour afficher toutes les formations désactivées.
    """
    formations = Formation.objects.filter(est_active=False)
    context = {
        'formations': formations,
        'titre_page': 'Formations désactivées',
    }
    return render(request, 'gestion_formations/formation_list.html', context)


# detail d'une formation:
#------------------------

def formation_detail(request, pk):
     """
     Vue basée sur une fonction pour afficher le détail d'une formation.
     """
     # Tente de récupérer la formation avec la clé primaire 'pk' ou retourne une page 404 si elle n'existe pas
     formation = get_object_or_404(Formation, pk=pk)
     
     # Récupère les sessions associées avec leur statut
     sessions = formation.sessions.all().select_related('instructor_principal')
    

     context = {
        'formation': formation,
        'sessions': sessions,
        'titre_page': f'Détail de la formation : {formation.nom}',
        'session_count': sessions.count(),
        'active_session_count': sessions.filter(statut__in=['OPEN', 'IN_PROGRESS']).count(),
     }

     # Rend le template et lui passe le contexte
     return render(request, 'gestion_formations/formation_detail.html', context)

# cree une formation:
#--------------------

def formation_create(request):
    """
    Vue pour créer une nouvelle formation.
    """
    if request.method == 'POST':
        form = FormationForm(request.POST)
        if form.is_valid():
            # Sauvegarder la formation
            form.save()
            messages.success(request, "La formation a été créée avec succès.")
            return redirect('gestion_formations:formation_list')  # Redirige vers la liste des formations
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = FormationForm()

    context = {
        'form': form,
        'titre_page': 'Créer une formation',
    }
    return render(request, 'gestion_formations/formation_form.html', context)

# update formation:
#------------------

def formation_update(request, pk):
    """
    Vue pour mettre à jour une formation existante.
    """
    formation = get_object_or_404(Formation, pk=pk)

    if request.method == 'POST':
        form = FormationForm(request.POST, instance=formation)
        if form.is_valid():
            form.save()
            messages.success(request, "La formation a été mise à jour avec succès.")
            return redirect('gestion_formations:formation_list')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = FormationForm(instance=formation)

    context = {
        'form': form,
        'titre_page': f'Mettre à jour la formation : {formation.nom}',
    }
    return render(request, 'gestion_formations/formation_form.html', context)

# supprimer formation:
#---------------------

def formation_delete(request, pk):
    """
    Vue pour supprimer une formation.
    """
    formation = get_object_or_404(Formation, pk=pk)

    if request.method == 'POST':
        formation.delete()
        messages.success(request, "La formation a été supprimée avec succès.")
        return redirect('gestion_formations:formation_list')

    context = {
        'formation': formation,
        'titre_page': f'Confirmer la suppression de : {formation.nom}',
    }
    return render(request, 'gestion_formations/formation_confirm_delete.html', context)



# Session:
#----------------
# detail d'une Session :
#---------

#liste des sessions:
#-------------------
class SessionListView(ListView):
    """
    Vue pour afficher la liste de toutes les sessions.
    """
    model = Session              # Le modèle à lister
    template_name = 'gestion_formations/session_list.html' # Le template à utiliser
    context_object_name = 'sessions' # Le nom de la variable contenant la liste dans le template
    ordering = ['date_debut_session'] # Tri par défaut

    # Optionnel : Vous pouvez filtrer le queryset ici si nécessaire
    # Par exemple, pour n'afficher que les sessions ouvertes :
    # def get_queryset(self):
    #     return Session.objects.filter(statut=SessionStatus.OPEN)
    # Assurez-vous d'importer SessionStatus si vous filtrez par statut
    # from .models import Session, SessionStatus
    

# detail Session:
#----------------
class SessionDetailView(DetailView):
    model = Session
    template_name = 'gestion_formations/session_detail.html'
    context_object_name = 'session'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['seances'] = self.object.seances.all().order_by('date', 'heure_debut')
        return context


# creation Session:
#-----------------

class SessionCreateView(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    permission_required = 'gestion_formations.add_session'
    model = Session
    form_class = SessionForm
    template_name = 'gestion_formations/session_form.html'
    success_url = reverse_lazy('gestion_formations:list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
    
# update d'une Session:
#----------------------

class SessionUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    permission_required = 'gestion_formations.change_session'
    model = Session
    form_class = SessionForm
    template_name = 'gestion_formations/session_form.html'

    def get_success_url(self):
        return reverse_lazy('gestion_formations:session_detail', kwargs={'pk': self.object.pk})
    
# supprimer Session:
#-------------------

class SessionDeleteView(DeleteView):
    model = Session
    template_name = 'gestion_formations/session_confirm_delete.html'
    success_url = reverse_lazy('gestion_formations:list')
    
# Vue spéciale pour créer une Session sous une Formation:
#--------------------------------------------------------

class SessionCreateForFormationView(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    permission_required = 'gestion_formations.add_session'
    model = Session
    form_class = SessionForm
    template_name = 'gestion_formations/session_form.html'

    def dispatch(self, request, *args, **kwargs):
        # Récupère la formation à partir de l'URL
        self.formation = get_object_or_404(Formation, pk=self.kwargs['formation_pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.formation = self.formation  # lier la session à la formation
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formation'] = self.formation
        return context

    def get_success_url(self):
        return reverse_lazy('gestion_formations:formation_detail', kwargs={'pk': self.formation.pk})
    
    
    

    
# Seance:
#--------


# creation seance:
#-----------------

#class SeanceCreateView(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
#    permission_required = 'gestion_formations.add_seance'
#    model = Seance
#    form_class = SeanceForm
#    template_name = 'gestion_formations/seance_form.html'

#    def get_form_kwargs(self):
#        kwargs = super().get_form_kwargs()
#        kwargs['session_pk'] = self.kwargs['session_pk']
#        return kwargs

#    def form_valid(self, form):
#        form.instance.created_by = self.request.user
#        return super().form_valid(form)

#    def get_success_url(self):
#        return reverse_lazy('gestion_formations:session_detail', kwargs={'pk': self.object.session.pk})


#seance creation :
#----------------

class SeanceCreateView(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    permission_required = 'gestion_formations.add_seance'
    model = Seance
    form_class = SeanceForm
    template_name = 'gestion_formations/seance_form.html'

    def get_form_kwargs(self):
        """Transmet le session_pk au formulaire et définit l'utilisateur comme request"""
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'session_pk': self.kwargs['session_pk'],
            'request': self.request  # Pour accéder à l'utilisateur dans le formulaire
        })
        return kwargs

    def get_initial(self):
        """Valeurs par défaut intelligentes"""
        initial = super().get_initial()
        session = get_object_or_404(Session, pk=self.kwargs['session_pk'])
        
        # Calcul de la prochaine date disponible
        last_seance = Seance.objects.filter(session=session).order_by('-date').first()
        next_date = last_seance.date + timedelta(days=7) if last_seance else session.date_debut_session
        
        initial.update({
            'session': session,
            'date': max(next_date, timezone.now().date()),
            'heure_debut': time(9, 0),  # 09:00 par défaut
            'heure_fin': time(12, 0),    # 12:00 par défaut
            'instructor': session.instructor_principal  # Formateur principal par défaut
        })
        return initial

    def form_valid(self, form):
        """Validation et sauvegarde avec messages"""
        form.instance.created_by = self.request.user
        
        # Vérification des conflits
        conflits = form.instance.check_conflits()
        if conflits['instructor']:
            messages.warning(self.request, 
                f"Attention: Conflit de planning avec {conflits['instructor']}")
        if conflits['lieu']:
            messages.warning(self.request,
                f"Attention: Le lieu est déjà réservé pour {conflits['lieu']}")
        
        response = super().form_valid(form)
        messages.success(self.request, "Séance créée avec succès!")
        return response

    def get_success_url(self):
        """Redirection intelligente"""
        if 'save_and_add_another' in self.request.POST:
            return reverse('gestion_formations:seance_create', 
                         kwargs={'session_pk': self.object.session.pk})
        return reverse('gestion_formations:session_detail', 
                      kwargs={'pk': self.object.session.pk})

    def get_context_data(self, **kwargs):
        """Ajout d'informations contextuelles"""
        context = super().get_context_data(**kwargs)
        session = get_object_or_404(Session, pk=self.kwargs['session_pk'])
        context.update({
            'session': session,
            'title': f"Créer une séance pour {session.nom_session}",
            'available_rooms': self.get_available_rooms(),
            'instructor_schedule': self.get_instructor_schedule()
        })
        return context

    def get_available_rooms(self):
        """Liste des salles disponibles pour cette formation"""
        session = get_object_or_404(Session, pk=self.kwargs['session_pk'])
        return Room.objects.filter(
            capacity__gte=session.capacite_max
        ).exclude(
            unavailable_dates__contains=timezone.now().date()
        )
        
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
            # Gérer le cas où la session n'existe pas (erreur probable si session_id est incorrect)
            # Pour l'affichage des choix, on pourrait retourner un queryset vide ou toutes les salles si pas de capacité requise connue
            print(f"AVERTISSEMENT: Session with ID {session_id} not found.")
            capacite_requise = 0 # On suppose qu'on peut utiliser n'importe quelle salle si la session n'est pas trouvée ou n'a pas de capacité

        # Trouver les séances qui se chevauchent avec le créneau horaire donné à la même date
        # Condition de chevauchement : Début < Fin_Autre ET Fin > Début_Autre
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
        # 1. Elles doivent être assez grandes pour la capacité requise (si capacité_requise > 0)
        # 2. Elles ne doivent PAS être dans la liste des IDs de salles occupées (booked_room_ids)
        available_rooms_queryset = Room.objects.all()

        if capacite_requise > 0:
            available_rooms_queryset = available_rooms_queryset.filter(capacity__gte=capacite_requise)

        # Exclure les salles qui sont occupées à ce créneau
        available_rooms_queryset = available_rooms_queryset.exclude(pk__in=booked_room_ids)

        return available_rooms_queryset

    def get_instructor_schedule(self):
        """Emploi du temps du formateur principal"""
        session = get_object_or_404(Session, pk=self.kwargs['session_pk'])
        if not session.instructor_principal:
            return None
            
        return Seance.objects.filter(
            instructor=session.instructor_principal,
            date__gte=timezone.now().date()
        ).order_by('date', 'heure_debut')
    
    
# mise a jour seance:
#--------------------

class SeanceUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    permission_required = 'gestion_formations.change_seance'
    model = Seance
    form_class = SeanceForm
    template_name = 'gestion_formations/seance_form.html'

    def get_success_url(self):
        return reverse_lazy('gestion_formations:session_detail', kwargs={'pk': self.object.session.pk})

#supprimer seance:
#-----------------

class SeanceDeleteView(PermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    permission_required = 'gestion_formations.delete_seance'
    model = Seance
    template_name = 'gestion_formations/seance_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('gestion_formations:session_detail', kwargs={'pk': self.object.session.pk})

# detail seance:
#---------------

class SeanceDetailView(LoginRequiredMixin, DetailView):
    model = Seance
    template_name = 'gestion_formations/seance_detail.html'
    context_object_name = 'seance'
    


# gérer les séances d'une session:
#--------------------------------

class SessionSeancesView(ListView):
    model = Seance
    template_name = 'gestion_formations/session_seances.html'
    context_object_name = 'seances'

    def get_queryset(self):
        self.session = get_object_or_404(Session, pk=self.kwargs['session_pk'])
        return Seance.objects.filter(session=self.session).order_by('date', 'heure_debut')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['session'] = self.session
        context['calendar_url'] = reverse('gestion_formations:session_calendar', kwargs={'session_pk': self.session.pk})
        return context



# ajouter plusieur seances :
#---------------------------

# Optionnel : Définir le test de permission (par exemple, formateur ou admin)

def is_instructor_or_admin(user):
    # Assurez-vous que l'utilisateur est connecté ET qu'il a le rôle formateur ou admin
    # Cela suppose que votre CustomUser a les propriétés is_instructor et is_admin
    
    # return user.is_authenticated and (user.is_instructor or user.is_admin)
    return user.is_authenticated and  user.is_admin


@user_passes_test(is_instructor_or_admin)
def ajouter_plusieurs_seances(request, session_pk):
    """
    Vue pour ajouter plusieurs séances à une session spécifique en utilisant un formset.
    Accessible uniquement aux utilisateurs ayant le rôle INSTRUCTOR ou ADMIN.
    """
    # Récupère la session à laquelle on ajoute les séances
    session = get_object_or_404(Session, pk=session_pk)

    # Pour l'ajout, on initialise le formset avec un queryset vide
    # Si vous vouliez aussi modifier/supprimer les séances existantes pour cette session via ce formset,
    # le queryset devrait être : Seance.objects.filter(session=session)
    queryset = Seance.objects.none()

    if request.method == 'POST':
        # Lier les données POST et les fichiers au formset
        formset = SeanceFormSet(request.POST, request.FILES, queryset=queryset) # Passer le queryset

        if formset.is_valid():
            # Utilise une transaction atomique pour s'assurer que toutes les sauvegardes réussissent ou échouent ensemble
            with transaction.atomic():
                # Parcourt chaque formulaire dans le formset validé
                for form in formset:
                    # has_changed() vérifie si le formulaire (même un extra) a été rempli ou modifié
                    if form.has_changed():
                         # Crée l'instance de la séance mais ne la sauvegarde pas tout de suite (commit=False)
                        seance = form.save(commit=False)
                        # Assigne la séance à la session récupérée depuis l'URL
                        seance.session = session
                        # Optionnel : Attribuer l'utilisateur qui a créé la séance (si champ created_by existe)
                        # seance.created_by = request.user
                        # Sauvegarde l'instance de la séance dans la base de données
                        seance.save()

                # La gestion des suppressions via formset.save() n'est nécessaire que si can_delete=True
                # et que le queryset n'est pas vide (on gère des objets existants).
                # Ici, avec queryset=Seance.objects.none(), on ne fait que des créations.

            messages.success(request, f"Les séances pour la session '{session.nom_session}' ont été ajoutées avec succès.")
            # Redirige vers la page de détail de la session après succès
            return redirect('gestion_formations:session_detail', pk=session_pk)
            # Alternative : Rediriger vers la liste des séances pour cette session
            # return redirect('gestion_formations:seance_list', session_pk=session_pk)

        else:
            # Si le formset n'est pas valide, les erreurs seront attachées au formset et à chaque formulaire
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")

    else: # Méthode GET
        # Initialise le formset pour l'affichage (avec les formulaires extra vides)
        formset = SeanceFormSet(queryset=queryset) # Passer le queryset (vide ici)

    # Rend le template avec le formset et l'objet session
    context = {
        'formset': formset,
        'session': session, # Passe la session au template pour affichage
        'titre_page': f"Ajouter plusieurs séances pour la session '{session.nom_session}'"
    }
    return render(request, 'gestion_formations/seance_formset.html', context)



# salle Room:
#------------

def get_available_locations(self):
    session = get_object_or_404(Session, pk=self.kwargs['session_pk'])
    return Room.objects.filter(capacity__gte=session.capacite_max)


# Calendrier des Séances:
#-----------------------

class CalendarView(View):
    def get(self, request, *args, **kwargs):
        month = int(request.GET.get('month', date.today().month))
        year = int(request.GET.get('year', date.today().year))
        
        seances = Seance.objects.filter(
            date__year=year,
            date__month=month
        ).select_related('session', 'session__formation', 'instructor')
        
        events = []
        for seance in seances:
            events.append({
                'title': f"{seance.session.formation.nom} - {seance.sujet_aborde or 'Séance'}",
                'start': f"{seance.date.isoformat()}T{seance.heure_debut.isoformat()}",
                'end': f"{seance.date.isoformat()}T{seance.heure_fin.isoformat()}",
                'url': reverse('gestion_formations:seance_detail', kwargs={'pk': seance.pk}),
                'color': '#3a87ad' if not seance.est_annulee else '#bd362f',
            })
        
        return JsonResponse(events, safe=False)



# --- Nouvelle vue pour la page du calendrier ---

class SeanceCalendarPageView(LoginRequiredMixin, TemplateView):
    """
    Vue pour afficher la page HTML qui contiendra le calendrier des séances.
    """
    template_name = 'gestion_formations/seance_calendar_page.html'

    # Optionnel : ajouter le titre de la page au contexte
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre_page'] = "Calendrier des Séances"
        # Vous pourriez aussi passer l'URL de la source de données du calendrier
        context['calendar_data_url'] = reverse('gestion_formations:calendar_data')
        return context  
    


# Export des Données:
#-------------------

def export_sessions_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sessions_formation.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Formation', 'Session', 'Statut', 'Date début', 'Date fin', 'Formateur', 'Inscrits'])
    
    sessions = Session.objects.all().select_related('formation', 'instructor_principal')
    for session in sessions:
        writer.writerow([
            session.formation.nom,
            session.nom_session,
            session.get_statut_display(),
            session.date_debut_session,
            session.date_fin_session,
            session.instructor_principal.get_full_name() if session.instructor_principal else '',
            session.inscriptions.count(),
        ])
    
    return response



# Nous ajouterons d'autres vues ici plus tard