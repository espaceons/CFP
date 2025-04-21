from django.contrib import admin

from gestion_formations.models import Formation

# Register your models here.
admin.site.register(Formation) # Enregistre le modèle 'formations' pour qu'il soit visible dans l'admin