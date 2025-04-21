# gestion_users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

# Optionnel : Personnaliser l'affichage dans l'admin si besoin
# class CustomUserAdmin(UserAdmin):
#     list_display = UserAdmin.list_display + ('role',) # Ajoute le rôle à la liste

# admin.site.register(CustomUser, CustomUserAdmin)
# Ou simplement enregistrer le modèle sans personnalisation poussée au début :
admin.site.register(CustomUser)