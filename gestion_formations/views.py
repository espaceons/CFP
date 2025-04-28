# gestion_formations/views.py


from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import redirect, render, get_object_or_404 # get_object_or_404 est utile pour les vues basées sur des fonctions
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView

from gestion_users.views import FormateurCreationForm # Importe la vue générique DetailView
from .models import Formation, Seance, Session # Importe Formation et Session
from .forms import FormationForm, SeanceForm, SessionForm
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

class SessionDetailView(DetailView):
    model = Session
    template_name = 'gestion_formations/session_detail.html'
    context_object_name = 'session'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['seances'] = self.object.seances.all().order_by('date', 'heure_debut')
        return context

 
# ajouter formateur a partir de creation des session dans une formation :
#------------------------------------------------------------------------

@login_required
@permission_required('gestion_users.add_customuser', raise_exception=True)
def ajouter_formateur(request):
    """
    Vue pour ajouter un formateur (utilisateur avec rôle 'INSTRUCTOR')
    """
    if request.method == 'POST':
        form = FormateurCreationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Le formateur a été ajouté avec succès.")
            return redirect('gestion_users:user_list')
    else:
        form = FormateurCreationForm()

    context = {
        'form': form,
        'title': 'Ajouter un formateur'
    }
    return render(request, 'gestion_users/ajouter_formateur.html', context)



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

# creation Seance:
#-----------------

# creation seance:
#-----------------

class SeanceCreateView(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    permission_required = 'gestion_formations.add_seance'
    model = Seance
    form_class = SeanceForm
    template_name = 'gestion_formations/seance_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['session_pk'] = self.kwargs['session_pk']
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('gestion_formations:session_detail', kwargs={'pk': self.object.session.pk})

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
                'url': reverse('gestion_formations:seance_update', kwargs={'pk': seance.pk}),
                'color': '#3a87ad' if not seance.est_annulee else '#bd362f',
            })
        
        return JsonResponse(events, safe=False)
    
    


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