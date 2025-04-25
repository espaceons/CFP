# gestion_inscriptions/views.py

from django.shortcuts import render, get_object_or_404, redirect # Ajout redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, Http404 # Importe Http404 en plus # Peut-être utile pour des contrôles d'accès plus stricts
from django.conf import settings # Pour accéder à LOGIN_REDIRECT_URL ou d'autres paramètres
from django.contrib import messages # Pour ajouter des messages utilisateur

# Assurez-vous d'importer les modèles nécessaires depuis votre application et les autres apps
# Adaptez les chemins d'importation si vos modèles sont dans des sous-modules
from .models import Enrollment, Session, Student, Instructor # Importez les modèles de gestion_inscriptions
from gestion_users.models import CustomUser # Importez votre modèle utilisateur personnalisé
from gestion_formations.models import Formation # Importez le modèle Formation si Formation est dans gestion_formations





@login_required
def student_enrollments_view(request):
    """
    Vue pour afficher la liste des inscriptions de l'utilisateur connecté (s'il est étudiant).
    """
    user = request.user # L'utilisateur connecté

    # Tente de récupérer le profil étudiant lié. Redirige si le profil n'existe pas.
    try:
        student_profile = user.student # Accède au related_name='student' sur CustomUser
    except Student.DoesNotExist: # Capture l'exception si le profil Student n'est pas lié à ce CustomUser
        messages.warning(request, "Vous n'avez pas de profil étudiant associé à votre compte.")
        return redirect('gestion_users:profile') # Redirige vers la page de profil utilisateur par défaut
    except Exception as e:
         # Gérer d'autres erreurs potentielles lors de l'accès au profil
         messages.error(request, f"Une erreur est survenue lors de la récupération de votre profil étudiant : {e}")
         return redirect('gestion_users:profile') # Rediriger en cas d'erreur


    # Récupérer toutes les inscriptions liées à ce profil étudiant
    # Assurez-vous que votre modèle Enrollment a un ForeignKey vers Student nommé 'student'
    # Si le ForeignKey dans Enrollment est nommé 'student' et qu'il pointe vers Student,
    # et que le related_name dans Student pour ce ForeignKey est le défaut ('enrollment_set'),
    # vous pouvez accéder aux inscriptions comme ceci :
    enrollments = student_profile.enrollment_set.all().select_related('session', 'session__formation', 'evaluation_type')
    # Si vous aviez défini un related_name différent dans le ForeignKey sur Enrollment, utilisez ce nom :
    # related_name='inscriptions_etudiant' -> enrollments = student_profile.inscriptions_etudiant.all()

    context = {
        'student_profile': student_profile, # On passe aussi le profil étudiant si besoin dans le template
        'enrollments': enrollments, # Passe la QuerySet des inscriptions au template
        'titre_page': 'Mes Formations',
        'active_tab': 'my_enrollments', # Pour la sidebar si vous l'utilisez
    }

    return render(request, 'gestion_inscriptions/student_enrollments.html', context)








# ... vue enrollement_detail pour etudiant ...
#-------------------------------


@login_required
def enrollment_detail_view(request, pk):
    """
    Vue pour afficher les détails d'une inscription spécifique.
    Contrôle l'accès : seul l'étudiant concerné, un formateur (de la session), ou un admin peut voir les détails.
    """
    # Tente de récupérer l'inscription par son ID (pk). Utilise select_related pour optimiser l'accès aux modèles liés.
    # Note : get_object_or_404 lèvera une Http404 si l'objet n'existe pas.
    try:
        enrollment = get_object_or_404(
            Enrollment.objects.select_related('student__user', 'session__formation', 'session__instructor__user'), # Prépare les jointures
            pk=pk
        )
    except Exception as e:
        messages.error(request, f"Erreur lors de la récupération de l'inscription : {e}")
        # Rediriger vers la liste des inscriptions ou une page d'erreur
        return redirect('gestion_inscriptions:student_enrollments') # Rediriger vers la liste des inscriptions


    # --- Contrôle d'accès ---
    # Qui a le droit de voir cette page d'inscription ?
    # 1. L'utilisateur connecté est l'étudiant concerné par l'inscription.
    is_student_concerned = (enrollment.student.user == request.user)

    # 2. L'utilisateur connecté est le formateur de la session liée à cette inscription.
    # Vérifie si la session a un formateur et si l'utilisateur connecté est ce formateur.
    is_instructor_concerned = False
    if enrollment.session.instructor: # S'assure qu'il y a bien un formateur assigné à la session
        is_instructor_concerned = (enrollment.session.instructor.user == request.user)

    # 3. L'utilisateur connecté est staff ou superuser (peut tout voir).
    is_staff_or_superuser = request.user.is_staff or request.user.is_superuser


    # Si l'utilisateur n'est aucun de ceux autorisés, refuser l'accès
    if not (is_student_concerned or is_instructor_concerned or is_staff_or_superuser):
        # messages.warning(request, "Vous n'êtes pas autorisé à voir les détails de cette inscription.")
        return HttpResponseForbidden("Vous n'êtes pas autorisé à voir cette inscription.") # Retourne une erreur 403 Forbidden


    # Récupérer les évaluations liées à cette inscription (si vous voulez les afficher)
    # Assurez-vous que votre modèle Evaluation a un ForeignKey vers Enrollment
    evaluations = enrollment.evaluation_set.all().select_related('evaluation_type', 'seance') # Prépare les jointures


    context = {
        'enrollment': enrollment, # Passe l'objet inscription au template
        'evaluations': evaluations, # Passe les évaluations liées
        'titre_page': f"Détails de l'inscription #{enrollment.pk}", # Titre dynamique
        'is_student_concerned': is_student_concerned, # Pour afficher des infos spécifiques dans le template si c'est l'étudiant
        'is_instructor_concerned': is_instructor_concerned, # Pour afficher des infos spécifiques si c'est le formateur
    }

    return render(request, 'gestion_inscriptions/enrollment_detail.html', context)


# Vous pouvez ajouter ici d'autres vues pour gestion_inscriptions, comme les détails d'une inscription, etc.
# Exemple :
# @login_required
# def enrollment_detail_view(request, pk):
#    enrollment = get_object_or_404(Enrollment.objects.select_related('student__user', 'session__formation'), pk=pk)
#    # S'assurer que l'utilisateur connecté est bien l'étudiant concerné ou un admin/staff
#    if not (request.user.is_staff or enrollment.student.user == request.user):
#        return HttpResponseForbidden("Vous n'êtes pas autorisé à voir cette inscription.")
#    context = {'enrollment': enrollment, 'titre_page': f"Inscription #{pk}"}
#    return render(request, 'gestion_inscriptions/enrollment_detail.html', context)




@login_required
def instructor_sessions_view(request):
    """
    Vue pour afficher la liste des sessions enseignées par l'utilisateur connecté (s'il est formateur).
    """
    user = request.user # L'utilisateur connecté

    # Tente de récupérer le profil formateur lié. Redirige si le profil n'existe pas.
    try:
        instructor_profile = user.instructor # Accède au related_name='instructor' sur CustomUser
    except Instructor.DoesNotExist: # Capture l'exception si le profil Instructor n'est pas lié
        messages.warning(request, "Vous n'avez pas de profil formateur associé à votre compte.")
        return redirect('gestion_users:profile') # Redirige vers la page de profil utilisateur
    except Exception as e:
         # Gérer d'autres erreurs potentielles
         messages.error(request, f"Une erreur est survenue lors de la récupération de votre profil formateur : {e}")
         return redirect('gestion_users:profile') # Rediriger en cas d'erreur


    # Récupérer toutes les sessions où ce formateur est assigné
    # Assurez-vous que votre modèle Session a un ForeignKey vers Instructor nommé 'instructor'
    # Si le ForeignKey dans Session est nommé 'instructor' et qu'il pointe vers Instructor,
    # et que le related_name dans Instructor pour ce ForeignKey est le défaut ('session_set'),
    # vous pouvez accéder aux sessions comme ceci :
    sessions_enseignees = instructor_profile.session_set.all().select_related('formation')
     # Si vous aviez défini un related_name différent dans le ForeignKey sur Session, utilisez ce nom :
    # related_name='cours_enseignes' -> sessions_enseignees = instructor_profile.cours_enseignes.all()


    context = {
        'instructor_profile': instructor_profile, # On passe aussi le profil formateur si besoin
        'sessions_enseignees': sessions_enseignees, # Passe la QuerySet des sessions au template
        'titre_page': 'Mes Cours Enseignés',
        'active_tab': 'my_sessions', # Pour la sidebar
    }

    return render(request, 'gestion_inscriptions/instructor_sessions.html', context)






@login_required # ou non, selon si les détails de session sont publics ou non
def session_detail_view(request, pk):
    """
    Vue pour afficher les détails d'une session spécifique.
    Peut afficher la liste des inscrits si l'utilisateur est le formateur ou un admin.
    """
    # Tente de récupérer la session par son ID (pk). Utilise select_related pour optimiser l'accès aux modèles liés.
    try:
        session = get_object_or_404(
            Session.objects.select_related('formation', 'instructor__user'), # Prépare les jointures
            pk=pk
        )
    except Exception as e:
        messages.error(request, f"Erreur lors de la récupération de la session : {e}")
        # Rediriger vers la liste des sessions ou une page d'erreur
        return redirect('gestion_inscriptions:instructor_sessions') # Rediriger vers la liste des sessions enseignées (ou autre page)


    # Qui a le droit de voir les détails complets (par ex. la liste des inscrits) ?
    # Le formateur assigné à cette session ou un admin/staff
    can_see_inscrits = False
    if request.user.is_staff or request.user.is_superuser:
        can_see_inscrits = True
    elif session.instructor and session.instructor.user == request.user:
        can_see_inscrits = True

    # Récupérer la liste des inscriptions pour cette session si l'utilisateur est autorisé à la voir
    inscriptions_session = None
    if can_see_inscrits:
        # Utilise prefetch_related pour récupérer les étudiants inscrits et leurs utilisateurs liés (optimisation)
        inscriptions_session = session.enrollment_set.all().select_related('student__user', 'evaluation_type') # Accède aux inscriptions via le related_name par défaut


    context = {
        'session': session, # Passe l'objet session au template
        'inscriptions_session': inscriptions_session, # Passe la liste des inscriptions (None si non autorisé/non applicable)
        'titre_page': f"Détails de la session : {session.nom_session}", # Titre dynamique
        'can_see_inscrits': can_see_inscrits, # Indique au template si la liste des inscrits doit être affichée
    }

    return render(request, 'gestion_inscriptions/session_detail.html', context)