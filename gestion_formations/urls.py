# gestion_formations/urls.py

from django.urls import path
from . import views  # Importe les vues de l'application courante
from gestion_formations.views import CalendarView, SeanceCalendarPageView, SessionCreateForFormationView, SessionListView
# Définit l'espace de noms de l'application (utile si vous avez plusieurs apps avec des noms d'URL similaires)
app_name = 'gestion_formations'

urlpatterns = [

    # URL pour la page d'accueil de l'application
    # Formattion.
    path('', views.formation_list, name='formation_list'),
    path('inactive/', views.formation_inactive_list,
         name='formation_inactive_list'),
    path('formation/<int:pk>/', views.formation_detail, name='formation_detail'),
    path('formation/create/', views.formation_create, name='formation_create'),
    path('formation/<int:pk>/update/',
         views.formation_update, name='formation_update'),
    path('formation/<int:pk>/delete/',
         views.formation_delete, name='formation_delete'),

    # Sessions
    # URL pour afficher la liste de toutes les sessions
    path('sessions/', SessionListView.as_view(), name='session_list'),
    path('session/<int:pk>/', views.SessionDetailView.as_view(),
         name='session_detail'),
    path('session/ajouter/', views.SeanceCreateView.as_view(), name='session_create'),
    path('session/<int:pk>/modifier/',
         views.SessionUpdateView.as_view(), name='session_update'),
    path('session/<int:pk>/supprimer/',
         views.SessionDeleteView.as_view(), name='session_delete'),

    # Url spéciale pour créer une Session sous une Formation
    path('formation/<int:formation_pk>/session/add/',
         SessionCreateForFormationView.as_view(), name='session_add_to_formation'),


    # Séances
    path('session/<int:session_pk>/seance/ajouter/',
         views.SeanceCreateView.as_view(), name='seance_create'),
    path('session/<int:session_pk>/seance/<int:pk>/modifier/',
         views.SeanceUpdateView.as_view(), name='seance_update'),
    path('seance/<int:session_pk>/seance/<int:pk>/supprimer/',
         views.SeanceDeleteView.as_view(), name='seance_delete'),
    path('seance/<int:session_pk>/seances/<int:pk>/',
         views.SeanceDetailView.as_view(), name='seance_detail'),

    # URL pour ajouter PLUSIEURS séances à une session (vue fonctionnelle)
    path('sessions/<int:session_pk>/seances/ajouter_multiple/',
         views.ajouter_plusieurs_seances, name='seance_create_multiple'),

    # Routes pour Room (Classe)
    path('rooms/', views.RoomListView.as_view(), name='room_list'),
    path('rooms/ajouter/', views.RoomCreateView.as_view(), name='room_create'),
    path('rooms/<int:pk>/', views.RoomDetailView.as_view(), name='room_detail'),
    path('rooms/<int:pk>/modifier/',
         views.RoomUpdateView.as_view(), name='room_update'),
    path('rooms/<int:pk>/supprimer/',
         views.RoomDeleteView.as_view(), name='room_delete'),



    # calendrier
    # URL pour la vue calendrier (source de données JSON pour le frontend)
    path('calendar/data/', CalendarView.as_view(), name='calendar_data'),

    # Nouvelle URL pour la page qui affiche le calendrier interactif
    path('calendar/', SeanceCalendarPageView.as_view(),
         name='seance_calendar_page'),

    # Nous ajouterons d'autres URLs ici plus tard (détail, création, etc.)
]
