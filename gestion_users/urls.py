# gestion_users/urls.py

from django.urls import path, include
from django.contrib.auth import views as auth_views # Importe les vues d'authentification de Django
from . import views # Importe les vues de l'application courante

app_name = 'gestion_users'

urlpatterns = [
    # URLs d'authentification intégrées de Django
    # Elles utilisent des vues génériques fournies par Django
    # Les templates par défaut sont dans registration/login.html, registration/logout.html, etc.
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    # Ajoutez d'autres URLs d'auth si besoin (password_reset, password_change, etc.)
    # path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    # ... etc ...

    # URL pour la page de profil de l'utilisateur connecté
    path('profile/', views.profile_view, name='profile'),

    # Si vous implémentez une page d'inscription (signup), son URL irait ici
    # path('signup/', views.signup_view, name='signup'),
]