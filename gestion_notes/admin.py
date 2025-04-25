# gestion_notes/admin.py

from django.contrib import admin
from .models import EvaluationType, Evaluation

# Optionnel : Personnaliser l'affichage
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'evaluation_type', 'note', 'date_evaluation')
    list_filter = ('evaluation_type', 'enrollment__session__formation', 'enrollment__session') # Filtrer par type, formation, session
    search_fields = ('enrollment__student__user__first_name', 'enrollment__student__user__last_name', 'evaluation_type__nom')
    # Si vous avez ajouté le champ 'seance' :
    list_filter = ('evaluation_type', 'enrollment__session__formation', 'enrollment__session', 'seance')
    search_fields = ('enrollment__student__user__first_name', 'enrollment__student__user__last_name', 'evaluation_type__nom', 'seance__date')
    
    
admin.site.register(Evaluation, EvaluationAdmin) # , EvaluationAdmin si vous avez personnalisé


# --- Configuration Admin pour le modèle EvaluationType ---

# Optionnel : Personnaliser l'affichage du modèle EvaluationType
class EvaluationTypeAdmin(admin.ModelAdmin):
    # Afficher le nom et la description dans la liste
    # Assume que le modèle EvaluationType a des champs 'nom' et 'description'
    list_display = ('nom', 'description')

    # Permettre de rechercher par nom ou description
    search_fields = ('nom', 'description')

    # Optionnel : Ajouter des filtres si EvaluationType avait des champs catégoriels (moins courant pour un type simple)
    # list_filter = ('is_active',) # Exemple si un champ is_active existait

    # Optionnel : Définir l'ordre d'affichage par défaut
    ordering = ('nom',) # Trie par nom par défaut

    # Optionnel : Personnaliser les champs affichés dans le formulaire d'ajout/modification
    # fields = ('nom', 'description') # Affiche seulement nom et description dans le formulaire


# Enregistrez le modèle EvaluationType avec sa classe d'administration personnalisée
# Remplacez "EvaluationTypeAdmin" par "None" ici si vous ne voulez PAS la personnalisation ci-dessus
admin.site.register(EvaluationType, EvaluationTypeAdmin)

# Assurez-vous que Evaluation est également enregistré si vous le faites dans ce fichier
# admin.site.register(Evaluation, EvaluationAdmin) # Déjà fait ci-dessus, assurez-vous qu'il n'est enregistré qu'UNE fois

# Si vous avez d'autres modèles dans gestion_notes, enregistrez-les aussi
# from .models import AutreModele # Exemple
# admin.site.register(AutreModele)

 

# Optionnel : Gérer les évaluations directement depuis l'inscription (dans l'admin de gestion_inscriptions)
# Vous devriez ajouter ceci dans gestion_inscriptions/admin.py si vous le souhaitez
# from gestion_notes.models import Evaluation as EvaluationModel # Renommer l'import

# class EvaluationInlineForEnrollment(admin.TabularInline):
#     model = EvaluationModel
#     extra = 0
#     fields = ('evaluation_type', 'note', 'date_evaluation', 'commentaires')
#     # Si vous avez le champ 'seance' :
#     # fields = ('seance', 'evaluation_type', 'note', 'date_evaluation', 'commentaires')

# Dans la classe EnrollmentAdmin de gestion_inscriptions/admin.py, ajouter :
# inlines = [AttendanceInline, EvaluationInlineForEnrollment]