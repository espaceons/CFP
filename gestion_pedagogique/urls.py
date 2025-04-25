"""
URL configuration for gestion_pedagogique project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # URL pour la page d'accueil de l'application gestion_users
    path('', include('gestion_users.urls', namespace='gestion_users')), # Inclut les URLs de l'application gestion_users
    
    # URL pour la page d'administration de Django
    path('admin/', admin.site.urls),
    
    # Inclut les URLs de l'application gestion_formations sous le préfixe '/formations/'
    path('formations/', include('gestion_formations.urls', namespace='gestion_formations')),
    
    # Vous inclurez les URLs des autres applications ici plus tard

    path('inscriptions/', include('gestion_inscriptions.urls', namespace='gestion_inscriptions')),
    # path('notes/', include('gestion_notes.urls', namespace='gestion_notes')),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
