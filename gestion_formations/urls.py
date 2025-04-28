# gestion_formations/urls.py

from django.urls import path
from . import views # Importe les vues de l'application courante
from gestion_formations.views import SessionCreateForFormationView
# Définit l'espace de noms de l'application (utile si vous avez plusieurs apps avec des noms d'URL similaires)
app_name = 'gestion_formations'

urlpatterns = [
    
    # URL pour la page d'accueil de l'application
    # Formattion.
    path('', views.formation_list, name='formation_list'),
    path('inactive/', views.formation_inactive_list, name='formation_inactive_list'),
    path('formation/<int:pk>/', views.formation_detail, name='formation_detail'),
    path('formation/create/', views.formation_create, name='formation_create'),
    path('formation/<int:pk>/update/', views.formation_update, name='formation_update'),
    path('formation/<int:pk>/delete/', views.formation_delete, name='formation_delete'),
    
    # ajouter formateur
    path('ajouter_formateur/', views.ajouter_formateur, name='ajouter_formateur'),
    
    # Sessions
    path('session/<int:pk>/', views.SessionDetailView.as_view(), name='session_detail'),
    path('session/ajouter/', views.SessionCreateView.as_view(), name='session_create'),
    path('session/<int:pk>/modifier/', views.SessionUpdateView.as_view(), name='session_update'),
    path('session/<int:pk>/supprimer/', views.SessionDeleteView.as_view(), name='session_delete'),
    
    # Url spéciale pour créer une Session sous une Formation
    path('formation/<int:formation_pk>/session/add/', SessionCreateForFormationView.as_view(), name='session_add_to_formation'),
    
    
    # Séances
    path('session/<int:session_pk>/seance/ajouter/', views.SeanceCreateView.as_view(), name='seance_create'),
    path('seance/<int:pk>/modifier/', views.SeanceUpdateView.as_view(), name='seance_update'),
    path('seance/<int:pk>/supprimer/', views.SeanceDeleteView.as_view(), name='seance_delete'),
    path('seance/<int:pk>/', views.SeanceDetailView.as_view(), name='seance_detail'),
    
    
    
    # Nous ajouterons d'autres URLs ici plus tard (détail, création, etc.)
]