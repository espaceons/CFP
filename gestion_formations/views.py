# gestion_formations/views.py

from django.shortcuts import render, get_object_or_404 # get_object_or_404 est utile pour les vues basées sur des fonctions
from django.views.generic import DetailView # Importe la vue générique DetailView
from .models import Formation, Session # Importe Formation et Session

def formation_list(request):
    """
    Vue pour afficher la liste de toutes les formations actives.
    """
    # Récupère tous les objets Formation qui sont actifs depuis la base de données
    formations = Formation.objects.filter(est_active=True)

    # Prépare le contexte (les données à passer au template)
    context = {
        'formations': formations,
        'titre_page': 'Liste des formations disponibles' # Un titre pour la page
    }

    # Rend le template 'gestion_formations/formation_list.html'
    # et lui passe le contexte
    return render(request, 'gestion_formations/formation_list.html', context)



# VUE basée sur une classe pour le détail:
#-------------------------------------------------
# class FormationDetailView(DetailView):
#     """
#     Vue pour afficher le détail d'une seule formation.
#     Utilise la vue générique DetailView.
#     """
#     model = Formation # Le modèle dont on veut afficher un objet
#     template_name = 'gestion_formations/formation_detail.html' # Le template à utiliser

    # Par défaut, DetailView récupère l'objet basé sur la clé primaire (pk)
    # capturée dans l'URL et la passe au template sous le nom 'object'
    # ou le nom du modèle en minuscules ('formation').
    # On peut aussi personnaliser le nom du contexte si on préfère :
    # context_object_name = 'ma_super_formation' # Alors on utiliserait {{ ma_super_formation }} dans le template

    # Optionnel : Surcharger get_queryset si on veut filtrer les objets affichables (ex: ne montrer que les formations actives)
    # def get_queryset(self):
    #     return Formation.objects.filter(est_active=True)

    # Optionnel : Ajouter du contexte supplémentaire
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     # L'objet formation est déjà dans le contexte (par défaut sous le nom 'formation')
    #     # On peut ajouter d'autres données si besoin, par exemple, les sessions liées si elles n'étaient pas déjà accessibles via related_name
    #     # context['sessions_de_la_formation'] = self.object.sessions.all() # Pas nécessaire si related_name est bien défini et que sessions est accessible directement
    #     return context


# Alternative : Vue basée sur une fonction pour le détail (moins de code "automatique" que DetailView)
def formation_detail(request, pk):
     """
     Vue basée sur une fonction pour afficher le détail d'une formation.
     """
     # Tente de récupérer la formation avec la clé primaire 'pk' ou retourne une page 404 si elle n'existe pas
     formation = get_object_or_404(Formation, pk=pk)

     context = {
         'formation': formation, # Passe l'objet formation au template
         'titre_page': f'Détail de la formation : {formation.nom}'
     }

     # Rend le template et lui passe le contexte
     return render(request, 'gestion_formations/formation_detail.html', context)



# Nous ajouterons d'autres vues ici plus tard