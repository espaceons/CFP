from django import forms
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from gestion_inscriptions.models import Instructor, Student
from gestion_users.models import CustomUser, UserRole
# Nous allons créer ce formulaire
from .forms import CustomAuthenticationForm, CustomUserCreationForm, UserProfileForm
from django.contrib.auth.decorators import login_required, user_passes_test

# Importe settings pour accéder aux variables de configuration
from django.conf import settings


# --- NOUVELLES VUES PERSONNALISÉES POUR CONNEXION/DÉCONNEXION ---
@require_http_methods(["GET", "POST"])
def custom_login_view(request):
    """
    Vue personnalisée pour la connexion des utilisateurs
    """
    if request.user.is_authenticated:
        return redirect('gestion_users:profile')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)

            if user is not None:

                login(request, user)

                # Vérifie si le champ 'remember_me' existe et est coché dans le formulaire validé
                # Répète cette ligne pour plus de clarté si besoin
                remember_me = form.cleaned_data.get('remember_me')
                if remember_me:
                    # Si "Se souvenir de moi" est coché, la session dure settings.SESSION_COOKIE_AGE
                    request.session.set_expiry(settings.SESSION_COOKIE_AGE)
                else:
                    # Sinon, la session expire à la fermeture du navigateur
                    request.session.set_expiry(0)
                # --- FIN LOGIQUE REMEMBER ME ---

                # messages.success(request, f"Bienvenue {user.get_full_name()} !")
                next_url = request.GET.get('next', 'gestion_users:profile')
                return redirect(next_url)
            else:
                messages.error(request, "Identifiants invalides.")
        else:
            messages.error(
                request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = CustomAuthenticationForm(request)

    context = {
        'form': form,
        'title': 'Connexion'
    }
    return render(request, 'gestion_users/login.html', context)


@require_http_methods(["GET"])
def custom_logout_view(request):
    """
    Vue personnalisée pour la déconnexion des utilisateurs
    """
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect('gestion_users:login')


# --- VUE POUR L'INSCRIPTION ---

def signup_view(request):
    """
    Vue pour permettre à un nouvel utilisateur de créer un compte, y compris l'upload de photo.
    """
    # Optionnel : Rediriger si déjà connecté
    if request.user.is_authenticated:
        # Logique de redirection sécurisée si déjà connecté (comme dans custom_login_view)
        next_url_auth = request.GET.get('next') or request.POST.get('next')
        # Importation si non déjà faite
        from django.utils.http import url_has_allowed_host_and_scheme
        if next_url_auth and url_has_allowed_host_and_scheme(
            url=next_url_auth,
            allowed_hosts=request.get_host(),
            require_https=request.is_secure()
        ):
            return redirect(next_url_auth)
        else:
            return redirect(settings.LOGIN_REDIRECT_URL)

    if request.method == 'POST':
        # Si le formulaire est soumis, l'instancier avec POST ET FILES
        # --- IMPORTANT : PASSER request.FILES ici ---
        # <-- PASSER request.FILES ici
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            # Si les données du formulaire sont valides (y compris la photo)
            user = form.save()  # Sauvegarde le nouvel utilisateur, y compris le fichier photo uploadé

            # Optionnel : Gérer la création automatique d'un profil Student ou Instructor
            # C'est une logique plus avancée. Souvent, les profils sont créés plus tard
            # (ex: quand un étudiant s'inscrit à une formation, ou un formateur est assigné à une session)
            # Si vous voulez les créer ici based on role, vous devez importer Student et Instructor
            # from gestion_inscriptions.models import Student, Instructor
            # if user.role == CustomUser.UserRole.STUDENT:
            #    Student.objects.create(user=user)
            # elif user.role == CustomUser.UserRole.INSTRUCTOR:
            #    Instructor.objects.create(user=user)

            # Optionnel : Connecter l'utilisateur immédiatement après l'inscription
            # Si vous activez ceci, assurez-vous d'importer 'login' depuis django.contrib.auth
            # login(request, user)
            # messages.success(request, f"Bienvenue {user.get_full_name() or user.username}, votre compte a été créé !")
            # return redirect(settings.LOGIN_REDIRECT_URL) # Rediriger après connexion auto

            # Si vous NE voulez PAS le connecter automatiquement :
            messages.success(
                request, "Votre compte a été créé avec succès ! Vous pouvez maintenant vous connecter.")
            # Rediriger vers la page de connexion après l'inscription
            return redirect('gestion_users:login')

        else:
            # Si le formulaire n'est pas valide
            messages.error(
                request, "Veuillez corriger les erreurs ci-dessous.")
            # Le template affichera les erreurs

    else:  # Si la requête est GET
        # Afficher le formulaire vide
        form = CustomUserCreationForm()

        # --- AJOUTEZ CETTE LIGNE POUR INSPECTER LE FORMULAIRE ---
        # print("Champs du formulaire d'inscription :", form.fields)
        # --- Fin Ligne à Ajouter ---

    # Rendre le template d'inscription en lui passant le formulaire
    context = {
        'form': form,
        'title': 'Créer un compte'
    }
    return render(request, 'gestion_users/signup.html', context)


# ... ( vue profile_view existante) ...
@login_required
def profile_view(request):
    """
    Vue pour afficher le profil de l'utilisateur connecté,
    y compris les informations spécifiques Student ou Instructor si elles existent.
    """
    user = request.user  # L'utilisateur connecté

    # Initialise les profils à None
    student_profile = None
    instructor_profile = None

    # --- TENTE DE RECUPERER LE PROFIL ETUDIANT (Indépendamment) ---
    # Utilise un bloc try...except pour gérer le cas où le profil lié n'existe pas
    try:
        # Accède au related_name='student' du OneToOneField sur CustomUser dans Student
        # Si le profil existe, student_profile contiendra l'objet Student
        student_profile = user.student
    except Student.DoesNotExist:
        # Si le profil n'existe pas pour cet utilisateur, l'exception est capturée et student_profile reste None
        pass
    # Capture d'autres exceptions potentielles (moins fréquent ici)
    except Exception as e:
        print(
            f"Erreur lors de la récupération du profil étudiant pour {user.username}: {e}")
        pass  # En cas d'erreur inattendue, le profil reste None

    # --- TENTE DE RECUPERER LE PROFIL FORMATEUR (Indépendamment) ---
    # Utilise un bloc try...except séparé pour le profil formateur
    try:
        # Accède au related_name='instructor' du OneToOneField sur CustomUser dans Instructor
        # Si le profil existe, instructor_profile contiendra l'objet Instructor
        instructor_profile = user.instructor
    except Instructor.DoesNotExist:
        # Si le profil n'existe pas pour cet utilisateur
        pass
    except Exception as e:  # Capture d'autres exceptions potentielles
        print(
            f"Erreur lors de la récupération du profil formateur pour {user.username}: {e}")
        pass  # En cas d'erreur inattendue, le profil reste None

    # Prépare le contexte à passer au template
    context = {
        'user': user,  # Passe l'objet utilisateur CustomUser
        # Passe l'objet Student s'il a été trouvé (sinon None)
        'student_profile': student_profile,
        # Passe l'objet Instructor s'il a été trouvé (sinon None)
        'instructor_profile': instructor_profile,
        'titre_page': 'Mon Profil',  # Titre de la page
        # Pour la navigation/mise en surbrillance dans le template (si utilisé)
        'active_tab': 'profile',
    }

    # Rend le template du profil
    return render(request, 'gestion_users/profile.html', context)


# ... ( vue edit_profile_view existante) ...

@login_required
def edit_profile_view(request):
    """
    Vue pour permettre à l'utilisateur connecté de modifier son profil.
    """
    user = request.user  # L'utilisateur connecté

    if request.method == 'POST':
        # Si la requête est POST, traiter le formulaire soumis
        # --- IMPORTANT : PASSER request.FILES au formulaire ---
        # C'est ce qui permet au formulaire de gérer les fichiers uploadés
        # <-- PASSER request.FILES ici
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            # Si le formulaire est valide (y compris le fichier photo si présent)
            # Sauvegarde les données du formulaire sur l'instance utilisateur, y compris le fichier
            user = form.save()
            messages.success(
                request, 'Votre profil a été mis à jour avec succès !')
            # Rediriger vers la page de profil après la sauvegarde
            return redirect('gestion_users:profile')
        else:
            # Si le formulaire n'est pas valide
            messages.error(
                request, "Veuillez corriger les erreurs ci-dessous.")
            # Le template affichera les erreurs grâce au contexte 'form'

    else:  # Si la requête est GET
        # Si la requête est GET, afficher le formulaire pré-rempli avec les données de l'utilisateur actuel
        form = UserProfileForm(instance=user)

    # Préparer le contexte pour le template
    context = {
        'form': form,
        'titre_page': 'Modifier mon Profil'
    }

    # Rendre le template edit_profile.html avec le formulaire
    return render(request, 'gestion_users/edit_profile.html', context)


# --- FONCTION DE VÉRIFICATION DE PERMISSION ---
# Utilisée pour restreindre l'accès aux listes sensibles (comme tous les formateurs)
def is_admin_or_staff(user):
    """Vérifie si l'utilisateur est un admin ou un membre du personnel."""
    # Assurez-vous que cette logique correspond à vos rôles CustomUser.UserRole
    return user.is_active and (user.is_staff or user.role == UserRole.ADMIN)


# --- VUES DE GESTION DES FORMATEURS  ---
@login_required
@user_passes_test(is_admin_or_staff)
def instructor_list_view(request):
    """Affiche la liste de tous les formateurs."""
    # Utilisation de select_related('user') pour optimiser l'accès aux données de l'utilisateur
    instructors = Instructor.objects.select_related(
        'user').all().order_by('user__last_name')

    context = {
        'instructor_list': instructors,
        'titre_page': 'Liste des Formateurs',
    }
    # Remarque : Le template sera dans gestion_users/templates/gestion_users/
    return render(request, 'gestion_users/instructor_list.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def instructor_detail_view(request, pk):
    """Affiche le profil détaillé d'un formateur."""
    # get_object_or_404 trouve l'objet Instructor par sa clé primaire (pk)
    instructor = get_object_or_404(
        Instructor.objects.select_related('user'), pk=pk)

    context = {
        'instructor': instructor,
        'titre_page': f'Profil de {instructor.user.get_full_name() or instructor.user.username}',
    }
    # Remarque : Le template sera dans gestion_users/templates/gestion_users/
    return render(request, 'gestion_users/instructor_detail.html', context)


@login_required
# Assurez-vous que is_admin_or_staff est défini
@user_passes_test(is_admin_or_staff)
def instructor_create_view(request):
    """
    Vue réservée aux administrateurs pour créer rapidement un nouvel Instructor.
    """

    # 1. Initialiser le rôle sur INSTRUCTOR (pour s'assurer qu'il est créé)
    initial_data = {'role': UserRole.INSTRUCTOR}

    if request.method == 'POST':
        # Passer les données POST et FILES, et l'initial_data pour définir le rôle
        form = CustomUserCreationForm(request.POST, request.FILES)

        # S'assurer que le rôle est bien forcé sur INSTRUCTOR avant la validation
        # (Si le rôle n'est pas caché dans le formulaire, l'utilisateur pourrait le changer)
        if 'role' in form.data:
            mutable_data = request.POST.copy()
            mutable_data['role'] = UserRole.INSTRUCTOR
            # Réinstancier avec rôle forcé
            form = CustomUserCreationForm(mutable_data)  # Réinstancier

        if form.is_valid():
            user = form.save()

            # Création automatique du profil Instructor
            Instructor.objects.create(user=user)

            messages.success(
                request, f"Le Formateur {user.username} a été créé avec succès.")
            return redirect('gestion_users:formateurs_list')

        else:
            messages.error(
                request, "Erreur dans la saisie. Veuillez vérifier les champs.")

    else:  # GET
        # Afficher le formulaire en initialisant le rôle sur INSTRUCTOR
        form = CustomUserCreationForm(initial=initial_data)

    context = {
        'form': form,
        'titre_page': 'Ajouter un nouveau Formateur',
        # Passer le rôle pour personnaliser le template si besoin
        'is_instructor_creation': True
    }
    return render(request, 'gestion_users/instructor_create.html', context)
