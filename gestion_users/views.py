# gestion_users/views.py

from django.shortcuts import render, redirect # Importe redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages # Optionnel : pour afficher des messages de succès/erreur
from .forms import UserProfileForm # Importe le formulaire créé dans forms.py
# from .models import CustomUser # Pas nécessaire d'importer le modèle ici

# ... (votre vue profile_view existante) ...
@login_required
def profile_view(request):
    user = request.user
    context = {
        'user': user,
        'titre_page': 'Mon Profil',
        # ... (autres profils si vous les passez) ...
    }
    return render(request, 'gestion_users/profile.html', context)


@login_required # Exige que l'utilisateur soit connecté pour accéder à cette vue
def edit_profile_view(request):
    """
    Vue pour permettre à l'utilisateur connecté de modifier son profil.
    """
    user = request.user # L'utilisateur à modifier est l'utilisateur connecté

    if request.method == 'POST':
        # Si la requête est POST, le formulaire est soumis
        # On l'instancie avec les données reçues (request.POST) et l'instance de l'utilisateur (request.user)
        form = UserProfileForm(request.POST, instance=user)
        # Si vous aviez aussi des FileFields (pour des images de profil par exemple), vous ajouteriez request.FILES :
        # form = UserProfileForm(request.POST, request.FILES, instance=user)

        if form.is_valid():
            # Si les données du formulaire sont valides
            form.save() # Sauvegarde les modifications sur l'instance de l'utilisateur
            messages.success(request, 'Votre profil a été mis à jour avec succès !') # Ajoute un message de succès (nécessite le framework messages)
            return redirect('gestion_users:profile') # Redirige l'utilisateur vers la page de profil après la sauvegarde

    else: # Si la requête n'est PAS POST (donc généralement GET)
        # On affiche le formulaire pré-rempli avec les données actuelles de l'utilisateur
        form = UserProfileForm(instance=user)

    context = {
        'form': form, # Passe le formulaire au template
        'titre_page': 'Modifier mon Profil'
    }

    # Rend le template 'gestion_users/edit_profile.html' en lui passant le formulaire
    return render(request, 'gestion_users/edit_profile.html', context)

# Vous ajouterez ici d'autres vues pour la gestion des utilisateurs (signup, etc.)
# def signup_view(request): ...