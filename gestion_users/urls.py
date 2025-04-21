# gestion_users/urls.py

from django.urls import path, include
from django.contrib.auth import views as auth_views # Importe les vues d'authentification de Django
from . import views # Importe les vues de l'application courante

app_name = 'gestion_users'

urlpatterns = [
        
    # --- URL POUR LA CONNEXION ---
    path('', views.custom_login_view, name='login'),
    path('logout/', views.custom_logout_view, name='logout'),
    # --- URL POUR L'INSCRIPTION ---
    path('signup/', views.signup_view, name='signup'), 
    
    # URLs pour la réinitialisation de mot de passe (vues intégrées de Django)
    # Ces vues attendent des templates spécifiques dans le sous-répertoire 'registration'
    path('password_reset/',
         auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'),
         name='password_reset'), # <--- C'est le nom d'URL que {% url %} recherche !

    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/', # Capture l'identifiant de l'utilisateur et le jeton
         auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'),
         name='password_reset_confirm'),

    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
         name='password_reset_complete'),

    # URL pour la page de profil de l'utilisateur connecté
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),


]