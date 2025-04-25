# gestion_formations/admin.py

from django.contrib import admin
from .models import Formation, Session, Seance # Importez aussi Seance

# Utilisation d'Inline pour gérer les Séances depuis la page Session
class SeanceInline(admin.TabularInline): # Utilisez TabularInline pour une table, StackedInline pour un formulaire complet par élément
    model = Seance
    extra = 1 # Nombre de formulaires de séance vides à afficher lors de l'ajout/modification d'une session
    # Optionnel : Personnaliser les champs affichés dans l'inline
    fields = ('date', 'heure_debut', 'heure_fin', 'instructor', 'lieu')


class SessionAdmin(admin.ModelAdmin):
    list_display = ('nom_session', 'formation', 'instructor_principal', 'date_debut_session', 'date_fin_session', 'capacite_max')
    list_filter = ('formation', 'instructor_principal', 'date_debut_session')
    search_fields = ('nom_session', 'formation__nom', 'instructor_principal__user__first_name', 'instructor_principal__user__last_name')
    inlines = [SeanceInline] # Associe les Séances à la Session dans l'admin


class FormationAdmin(admin.ModelAdmin):
    list_display = ('nom', 'est_active', 'duree_heures')
    search_fields = ('nom',)
    # Vous pourriez aussi vouloir un inline pour les sessions ici si vous le souhaitez
    # class SessionInlineForFormation(admin.TabularInline):
    #     model = Session
    #     extra = 0 # N'affiche pas de formulaire vide par défaut
    # FormationAdmin.inlines = [SessionInlineForFormation]

# Désenregistrez si déjà enregistré sans l'inline
# admin.site.unregister(Session)

admin.site.register(Formation, FormationAdmin)
admin.site.register(Session, SessionAdmin)
admin.site.register(Seance) # Enregistrez le modèle Seance pour y accéder directement aussi si besoin