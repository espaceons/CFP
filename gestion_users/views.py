from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .forms import CustomAuthenticationForm, CustomUserCreationForm, UserProfileForm  # Nous allons créer ce formulaire
from django.contrib.auth.decorators import login_required
from django.conf import settings # Importe settings pour accéder aux variables de configuration


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
                remember_me = form.cleaned_data.get('remember_me') # Répète cette ligne pour plus de clarté si besoin
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
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
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


# ... ( vue profile_view existante) ...
@login_required
def profile_view(request):
    user = request.user
    context = {
        'user': user,
        'title': 'Mon Profil', # Titre de la page
        'active_tab': 'profile'  # Pour la navigation dans le template
        # ... (autres profils si vous les passez) ...
    }
    return render(request, 'gestion_users/profile.html', context)


# --- VUE POUR L'INSCRIPTION ---

def signup_view(request):
    """
    permettre à un nouvel utilisateur de créer un compte.
    """
    # Optionnel : Si l'utilisateur est déjà connecté, le rediriger loin de la page d'inscription
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL) # Rediriger vers la page d'accueil ou profil


    if request.method == 'POST':
        # Si le formulaire est soumis
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Si les données du formulaire sont valides, créer l'utilisateur
            user = form.save() # Sauvegarde le nouvel utilisateur dans la base de données

            # Optionnel : Connecter l'utilisateur immédiatement après l'inscription
            # Vous pouvez choisir de ne pas le connecter automatiquement et le laisser se connecter via la page de login
            # Si vous voulez le connecter automatiquement :
            # login(request, user) # Connecte l'utilisateur
            # messages.success(request, f"Bienvenue {user.get_full_name() or user.username}, votre compte a été créé !")
            # return redirect(settings.LOGIN_REDIRECT_URL) # Rediriger après connexion auto


            # Si vous NE voulez PAS le connecter automatiquement :
            messages.success(request, "Votre compte a été créé avec succès ! Vous pouvez maintenant vous connecter.")
            # Rediriger vers la page de connexion après l'inscription
            return redirect('gestion_users:login')

    else: # Si la requête est GET
        # Afficher le formulaire vide
        form = CustomUserCreationForm()

    # Rendre le template d'inscription en lui passant le formulaire
    context = {
        'form': form,
        'title': 'Créer un compte'
    }
    return render(request, 'gestion_users/signup.html', context)


# ... ( vue edit_profile_view existante) ...
@login_required
def edit_profile_view(request):
    user = request.user
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre profil a été mis à jour avec succès !')
            return redirect('gestion_users:profile')
    else:
        form = UserProfileForm(instance=user)
    context = {
        'form': form,
        'titre_page': 'Modifier mon Profil'
    }
    return render(request, 'gestion_users/edit_profile.html', context)