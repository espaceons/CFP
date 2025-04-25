# gestion_inscriptions/admin.py

from django.contrib import admin
from .models import Instructor, Student

# Optionnel : Personnaliser l'affichage si besoin
class InstructorAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialite_enseignement')

class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'numero_etudiant', 'user__date_naissance') # specifier date de naissance de customuser


admin.site.register(Instructor, InstructorAdmin)
admin.site.register(Student, StudentAdmin)
# Ou simplement enregistrer les modèles :
# admin.site.register(Instructor)
# admin.site.register(Student)