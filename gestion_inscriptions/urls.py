# gestion_inscriptions/urls.py

from django.urls import path
from . import views # Importe les vues de l'application gestion_inscriptions

app_name = 'gestion_inscriptions' # Définir le namespace de l'application

urlpatterns = [
    # URL pour afficher les inscriptions de l'étudiant connecté
    path('mes-inscriptions/', views.student_enrollments_view, name='student_enrollments'),

    # URL pour afficher les sessions enseignées par le formateur connecté
    path('mes-sessions/', views.instructor_sessions_view, name='instructor_sessions'),

    # Vous pouvez ajouter d'autres URLs spécifiques à gestion_inscriptions ici
    path('inscription/<int:pk>/', views.enrollment_detail_view, name='enrollment_detail'), # Exemple
    path('session/<int:pk>/', views.session_detail_view, name='session_detail'), # Exemple
]