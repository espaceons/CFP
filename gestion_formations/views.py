# gestion_formations/views.py

from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q  # Déjà importé en haut
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, TemplateView, ListView
from django.utils import timezone
from datetime import timedelta, time, datetime, date
from django.db import transaction
from django.contrib.auth.decorators import user_passes_test, login_required, permission_required
from django.views.generic import CreateView, UpdateView, DeleteView
from django.core.paginator import Paginator
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.contrib import messages
import csv


# Importer les modèles et les formulaires
from .models import Formation, Room, Seance, Session
from .forms import FormationForm, RoomForm, SeanceForm, SeanceFormSet, SessionForm


# ====================================================================
# FORMATION VIEWS
# ====================================================================

# listes des formation:
# ----------------------
def formation_list(request):
    """Affiche la liste de toutes les formations actives avec recherche et pagination."""
    formations = Formation.objects.filter(est_active=True).order_by('nom')
    search_query = request.GET.get('search', '')
    if search_query:
        formations = formations.filter(
            Q(nom__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(objectifs__icontains=search_query)
        )
    paginator = Paginator(formations, 5)
    page_number = request.GET.get('page')
    formations_page = paginator.get_page(page_number)

    context = {
        'formations': formations_page,
        'titre_page': 'Liste des formations disponibles',
        'search_query': search_query,
    }
    return render(request, 'gestion_formations/formation_list.html', context)

# formation inactive liste:
# --------------------------


@login_required
@permission_required('gestion_formations.view_formation', raise_exception=True)
def formation_inactive_list(request):
    """
    Vue pour afficher toutes les formations désactivées (est_active=False), avec
    recherche et pagination. Nécessite une permission de vue.
    """
    formations = Formation.objects.filter(est_active=False).order_by('nom')

    # Fonctionnalité de recherche:
    search_query = request.GET.get('search', '')
    if search_query:
        formations = formations.filter(
            Q(nom__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(objectifs__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(formations, 5)  # 5 formations par page
    page_number = request.GET.get('page')
    formations_page = paginator.get_page(page_number)

    context = {
        'formations': formations_page,
        'titre_page': 'Formations désactivées',
        'search_query': search_query,
    }
    return render(request, 'gestion_formations/formation_list.html', context)


# detail d'une formation:
# ------------------------
def formation_detail(request, pk):
    """Affiche le détail d'une formation et ses sessions associées."""
    formation = get_object_or_404(Formation, pk=pk)
    sessions = formation.sessions.all().select_related(
        'instructor_principal').order_by('-date_debut_session')

    context = {
        'formation': formation,
        'sessions': sessions,
        'titre_page': f'Détail de la formation : {formation.nom}',
        'session_count': sessions.count(),
        'active_session_count': sessions.filter(statut__in=['OPEN', 'IN_PROGRESS']).count(),
    }
    return render(request, 'gestion_formations/formation_detail.html', context)


# cree une formation:
# --------------------
@login_required
@permission_required('gestion_formations.add_formation', raise_exception=True)
def formation_create(request):
    """Vue pour créer une nouvelle formation (basée sur une fonction)."""
    if request.method == 'POST':
        form = FormationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "La formation a été créée avec succès.")
            return redirect('gestion_formations:formation_list')
        else:
            messages.error(
                request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = FormationForm()

    context = {
        'form': form,
        'titre_page': 'Créer une formation',
    }
    return render(request, 'gestion_formations/formation_form.html', context)


# update formation:
# ------------------
@login_required
@permission_required('gestion_formations.change_formation', raise_exception=True)
def formation_update(request, pk):
    """Vue pour mettre à jour une formation existante (basée sur une fonction)."""
    formation = get_object_or_404(Formation, pk=pk)
    # ... (le reste de la fonction est correct) ...
    if request.method == 'POST':
        form = FormationForm(request.POST, instance=formation)
        if form.is_valid():
            form.save()
            messages.success(
                request, "La formation a été mise à jour avec succès.")
            return redirect('gestion_formations:formation_list')
        else:
            messages.error(
                request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = FormationForm(instance=formation)

    context = {
        'form': form,
        'titre_page': f'Mettre à jour la formation : {formation.nom}',
    }
    return render(request, 'gestion_formations/formation_form.html', context)


# supprimer formation:
# ---------------------
@login_required
@permission_required('gestion_formations.delete_formation', raise_exception=True)
def formation_delete(request, pk):
    """Vue pour supprimer une formation (basée sur une fonction)."""
    formation = get_object_or_404(Formation, pk=pk)
    # ... (le reste de la fonction est correct) ...
    if request.method == 'POST':
        formation.delete()
        messages.success(request, "La formation a été supprimée avec succès.")
        return redirect('gestion_formations:formation_list')

    context = {
        'formation': formation,
        'titre_page': f'Confirmer la suppression de : {formation.nom}',
    }
    return render(request, 'gestion_formations/formation_confirm_delete.html', context)


# ====================================================================
# SESSION VIEWS
# ====================================================================

# liste des sessions:
# -------------------
class SessionListView(ListView):
    model = Session
    template_name = 'gestion_formations/session_list.html'
    context_object_name = 'sessions'
    ordering = ['date_debut_session']


# detail Session:
# ----------------
class SessionDetailView(DetailView):
    model = Session
    template_name = 'gestion_formations/session_detail.html'
    context_object_name = 'session'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Assurez-vous d'utiliser le related_name 'seances' du modèle Session
        context['seances'] = self.object.seances.all().order_by('date',
                                                                'heure_debut')
        return context


# update d'une Session:
# ----------------------
class SessionUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    permission_required = 'gestion_formations.change_session'
    model = Session
    form_class = SessionForm
    template_name = 'gestion_formations/session_form.html'

    def get_success_url(self):
        return reverse_lazy('gestion_formations:session_detail', kwargs={'pk': self.object.pk})

# supprimer Session:
# -------------------


class SessionDeleteView(PermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    permission_required = 'gestion_formations.delete_session'
    model = Session
    template_name = 'gestion_formations/session_confirm_delete.html'
    # Correction de success_url
    success_url = reverse_lazy('gestion_formations:session_list')


# Vue spéciale pour créer une Session sous une Formation:
# --------------------------------------------------------
class SessionCreateForFormationView(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    permission_required = 'gestion_formations.add_session'
    model = Session
    form_class = SessionForm
    template_name = 'gestion_formations/session_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.formation = get_object_or_404(
            Formation, pk=self.kwargs['formation_pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.formation = self.formation
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formation'] = self.formation
        context['titre_page'] = f"Créer une session pour : {self.formation.nom}"
        return context

    def get_success_url(self):
        return reverse_lazy('gestion_formations:formation_detail', kwargs={'pk': self.formation.pk})


# ====================================================================
# SEANCE VIEWS
# ====================================================================

# seance creation :
# ----------------

# Utilisation de la classe SeanceCreateView unique et robuste

class SeanceCreateView(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    """
    Vue pour créer une séance individuelle liée à une session spécifique.
    Elle gère l'initialisation intelligente et la liaison à la session.
    """
    permission_required = 'gestion_formations.add_seance'
    model = Seance
    form_class = SeanceForm
    template_name = 'gestion_formations/seance_form.html'

    def get_form_kwargs(self):
        """Transmet le session_pk au formulaire pour le filtrage et l'initialisation."""
        kwargs = super().get_form_kwargs()
        # On passe le session_pk au formulaire pour qu'il puisse filtrer le queryset des salles
        kwargs['session_pk'] = self.kwargs['session_pk']
        # Passer la request est facultatif si le formulaire n'en a pas besoin explicitement
        # kwargs['request'] = self.request
        return kwargs

    def get_initial(self):
        """Définit les valeurs initiales pour les champs date, heure et instructeur."""
        initial = super().get_initial()
        session = get_object_or_404(Session, pk=self.kwargs['session_pk'])

        # Logique d'initialisation de la date basée sur la dernière séance (ou le début de session)
        last_seance = Seance.objects.filter(
            session=session).order_by('-date').first()

        # Date par défaut: 7 jours après la dernière séance, sinon le début de session
        if last_seance:
            next_date = last_seance.date + timedelta(days=7)
        else:
            next_date = session.date_debut_session

        # S'assurer que la date n'est pas dans le passé
        next_date = max(next_date, timezone.now().date())

        initial.update({
            # On ne met pas 'session' ici car on le gère dans form_valid et on le cache
            'date': next_date,
            'heure_debut': time(9, 0),
            'heure_fin': time(12, 0),
            'instructor': session.instructor_principal,
        })
        return initial

    def form_valid(self, form):
        """
        Définit l'objet Session pour la nouvelle Séance avant de sauvegarder.
        C'est l'étape CRITIQUE pour les champs HiddenInput/clés étrangères masquées.
        """
        try:
            session = Session.objects.get(pk=self.kwargs['session_pk'])
        except Session.DoesNotExist:
            # Gérer l'erreur si la session n'existe pas
            form.add_error(None, "La session parente n'existe pas.")
            return self.form_invalid(form)

        # Assigner la clé étrangère 'session' à l'instance du modèle
        form.instance.session = session

        # Optionnel: Assigner l'utilisateur créateur si vous utilisez created_by
        # if self.request.user.is_authenticated:
        #     form.instance.created_by = self.request.user

        # Sauvegarder l'instance maintenant que la clé étrangère est définie
        return super().form_valid(form)  # Ceci appelle form.save()

    # -----------------------------
    def form_invalid(self, form):
        # 🛑 AJOUTEZ UN AFFICHAGE D'ERREUR DANS LA CONSOLE 🛑
        print("--------------------------------")
        print("ERREURS DÉTAILLÉES DU FORMULAIRE :")
        print(form.errors.as_data())
        print("--------------------------------")

        # Retourne le formulaire avec les erreurs (qui devraient maintenant s'afficher dans le template)
        return super().form_invalid(form)
    # -----------------------------

    def get_success_url(self):
        """Redirection après succès (vers 'Ajouter une autre' ou le détail de session)."""
        if 'save_and_add_another' in self.request.POST:
            return reverse('gestion_formations:seance_create',
                           kwargs={'session_pk': self.object.session.pk})
        return reverse('gestion_formations:session_detail',
                       kwargs={'pk': self.object.session.pk})

    def get_context_data(self, **kwargs):
        """Ajout d'informations contextuelles (session et titre)."""
        context = super().get_context_data(**kwargs)
        context['session_pk'] = self.kwargs['session_pk']
        session = get_object_or_404(Session, pk=self.kwargs['session_pk'])
        context.update({
            'session': session,
            'title': f"Créer une séance pour {session.nom_session}",
            # Utilisation de la nouvelle méthode privée
            'instructor_schedule': self._get_instructor_schedule(session)
        })
        return context

    def _get_instructor_schedule(self, session):
        """Méthode privée pour récupérer l'emploi du temps du formateur principal."""
        if not session.instructor_principal:
            return Seance.objects.none()

        return Seance.objects.filter(
            instructor=session.instructor_principal,
            date__gte=timezone.now().date()
        ).order_by('date', 'heure_debut')


# mise a jour seance:
# --------------------
class SeanceUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    permission_required = 'gestion_formations.change_seance'
    model = Seance
    form_class = SeanceForm
    template_name = 'gestion_formations/seance_form.html'

    def get_form_kwargs(self):
        """Transmet le session_pk au formulaire pour le filtrage de la salle."""
        kwargs = super().get_form_kwargs()
        # En modification, le session_pk peut être tiré de l'instance existante
        kwargs['session_pk'] = self.object.session.pk
        return kwargs

    def get_success_url(self):
        messages.success(self.request, "Séance mise à jour avec succès!")
        return reverse_lazy('gestion_formations:session_detail', kwargs={'pk': self.object.session.pk})

# supprimer seance:
# -----------------


class SeanceDeleteView(PermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    permission_required = 'gestion_formations.delete_seance'
    model = Seance
    template_name = 'gestion_formations/seance_confirm_delete.html'

    def get_success_url(self):
        messages.success(self.request, "Séance supprimée avec succès!")
        return reverse_lazy('gestion_formations:session_detail', kwargs={'pk': self.object.session.pk})

# detail seance:
# ---------------


class SeanceDetailView(LoginRequiredMixin, DetailView):
    model = Seance
    template_name = 'gestion_formations/seance_detail.html'
    context_object_name = 'seance'

# gérer les séances d'une session:
# --------------------------------


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
        context['titre_page'] = f"Liste des séances pour {self.session.nom_session}"
        context['calendar_url'] = reverse('gestion_formations:session_calendar', kwargs={
                                          'session_pk': self.session.pk})
        return context


# ajouter plusieur seances :
# ---------------------------
# La vue `ajouter_plusieurs_seances` est conservée telle quelle car elle utilise le `SeanceFormSet`
# et gère correctement la liaison à la session dans `form.save(commit=False)`.

def is_instructor_or_admin(user):
    # Logique de permission simplifiée pour l'exemple (à adapter à vos rôles réels)
    return user.is_authenticated and user.is_staff


@user_passes_test(is_instructor_or_admin)
def ajouter_plusieurs_seances(request, session_pk):
    """Vue pour ajouter plusieurs séances à une session spécifique en utilisant un formset."""
    session = get_object_or_404(Session, pk=session_pk)
    queryset = Seance.objects.none()

    if request.method == 'POST':
        # NOTE: Pour que le SeanceForm dans le Formset puisse effectuer son filtrage
        # par capacité et période, il faut lui passer `form_kwargs`.
        formset = SeanceFormSet(
            request.POST,
            request.FILES,
            queryset=queryset,
            # Le SeanceFormSet a besoin de l'instance Session (parent)
            instance=session,
            # Il a également besoin du session_pk pour le filtrage interne dans SeanceForm
            form_kwargs={'session_pk': session_pk}
        )

        if formset.is_valid():
            with transaction.atomic():
                # Utiliser formset.save(commit=False) est la méthode la plus standard.
                # Elle retourne uniquement les instances des formulaires avec des données (qui ne sont pas marqués pour suppression).
                seances_a_sauvegarder = formset.save(commit=False)

                for seance in seances_a_sauvegarder:
                    # Assurez-vous d'assigner les champs qui ne sont pas dans les données POST (ou qui sont masqués)
                    if not seance.session_id:  # Pour une double sécurité si le champ 'session' n'était pas posté ou masqué
                        seance.session = session

                    seance.created_by = request.user
                    seance.save()

                # Sauvegarde des relations ManyToMany (si vous en aviez dans Seance)
                formset.save_m2m()

            messages.success(
                request, f"Les séances pour la session '{session.nom_session}' ont été ajoutées avec succès.")
            return redirect('gestion_formations:session_detail', pk=session_pk)
        else:
            messages.error(
                request, "Veuillez corriger les erreurs ci-dessous dans le formulaire.")

    else:
        # En méthode GET, on passe l'instance au FormSet si c'est un inlineformset_factory
        # ou le session_pk via form_kwargs pour un modelformset_factory (comme dans votre cas)
        formset = SeanceFormSet(
            queryset=queryset,
            form_kwargs={'session_pk': session_pk}
        )

    context = {
        'formset': formset,
        'session': session,
        'titre_page': f"Ajouter plusieurs séances pour la session '{session.nom_session}'"
    }
    return render(request, 'gestion_formations/seance_formset.html', context)

# ====================================================================
# Salle VIEWS
# ====================================================================

# --------------------------
# Liste des salles
# --------------------------


class RoomListView(LoginRequiredMixin, ListView):
    model = Room
    template_name = 'gestion_formations/room_list.html'
    context_object_name = 'rooms'
    ordering = ['name']
# --------------------------
# Création d'une salle
# --------------------------


class RoomCreateView(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    permission_required = 'gestion_formations.add_room'
    model = Room
    form_class = RoomForm
    template_name = 'gestion_formations/room_form.html'
    success_url = reverse_lazy('gestion_formations:room_list')
    # Assurez-vous que RoomForm existe et est correctement défini dans forms.py

# -----------------
# Détail d'une Salle
# -----------------


class RoomDetailView(LoginRequiredMixin, DetailView):
    """Affiche les détails d'une salle spécifique."""
    model = Room
    template_name = 'gestion_formations/room_detail.html'
    context_object_name = 'room'

# --------------------------
# Mise à jour d'une Salle
# --------------------------


class RoomUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    """Permet de modifier une salle existante."""
    permission_required = 'gestion_formations.change_room'
    model = Room
    form_class = RoomForm  # Assurez-vous d'avoir RoomForm dans forms.py
    template_name = 'gestion_formations/room_form.html'

    def get_success_url(self):
        # Redirige vers la vue de détail de la salle après modification
        messages.success(
            self.request, f"La salle '{self.object.name}' a été mise à jour avec succès.")
        return reverse_lazy('gestion_formations:room_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre_page'] = f"Modifier la salle : {self.object.name}"
        return context

# --------------------------
# Suppression d'une Salle
# --------------------------


class RoomDeleteView(PermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    """Permet de supprimer une salle existante."""
    permission_required = 'gestion_formations.delete_room'
    model = Room
    template_name = 'gestion_formations/room_confirm_delete.html'

    # Redirige vers la liste des salles après suppression
    success_url = reverse_lazy('gestion_formations:room_list')

    def form_valid(self, form):
        # Ajout d'un message avant la suppression
        messages.success(
            self.request, f"La salle '{self.object.nom}' a été supprimée avec succès.")
        return super().form_valid(form)


# ====================================================================
# UTILITY VIEWS (Rooms, Calendar, Export)
# ====================================================================


# Calendrier des Séances:
# -----------------------
class CalendarView(View):
    """API pour les données du calendrier (JSON)"""

    def get(self, request, *args, **kwargs):
        month = int(request.GET.get('month', date.today().month))
        year = int(request.GET.get('year', date.today().year))

        # Filtre optionnel par session_pk
        session_pk = kwargs.get('session_pk')

        seances = Seance.objects.filter(
            date__year=year,
            date__month=month
        ).select_related('session', 'session__formation', 'instructor')

        if session_pk:
            seances = seances.filter(session__pk=session_pk)

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


# Vue pour la page du calendrier général
class SeanceCalendarPageView(LoginRequiredMixin, TemplateView):
    template_name = 'gestion_formations/seance_calendar_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre_page'] = "Calendrier des Séances"
        context['calendar_data_url'] = reverse(
            'gestion_formations:calendar_data')
        return context

# Export des Données:
# -------------------


@login_required
@permission_required('gestion_formations.view_session', raise_exception=True)
def export_sessions_csv(request):
    """Exportation des données de sessions au format CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sessions_formation.csv"'

    writer = csv.writer(response)
    writer.writerow(['Formation', 'Session', 'Statut',
                    'Date début', 'Date fin', 'Formateur', 'Inscrits'])

    sessions = Session.objects.all().select_related(
        'formation', 'instructor_principal')
    for session in sessions:
        writer.writerow([
            session.formation.nom,
            session.nom_session,
            session.get_statut_display(),
            session.date_debut_session,
            session.date_fin_session,
            session.instructor_principal.get_full_name(
            ) if session.instructor_principal else '',
            session.inscriptions.count(),
        ])
    return response
