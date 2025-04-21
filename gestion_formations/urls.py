# gestion_formations/urls.py

from django.urls import path
from . import views # Importe les vues de l'application courante

# Définit l'espace de noms de l'application (utile si vous avez plusieurs apps avec des noms d'URL similaires)
app_name = 'gestion_formations'

urlpatterns = [
    
    # URL pour la page d'accueil de l'application
    # URL pour afficher la liste des formations.
    path('', views.formation_list, name='list'),
    # <int:pk> capture un entier (la clé primaire) et le passe à la vue
    path('<int:pk>/', views.formation_detail, name='detail'),
    # Nous ajouterons d'autres URLs ici plus tard (détail, création, etc.)
]