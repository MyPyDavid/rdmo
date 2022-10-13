from django.urls import re_path

from .views import CatalogsTableIndexView #SitesListView # CatalogsTableWrapperView
from .forms import CatalogsLockedFormView, CatalogsAvailableFormView, CatalogsSitesFormView


urlpatterns = [
    re_path(r'^$', CatalogsTableIndexView.as_view(), name='catalogs_table'),   
    re_path(r'(?P<pk>[0-9]+)/update/locked', CatalogsLockedFormView.as_view(), name='column_locked_form'),
    re_path(r'(?P<pk>[0-9]+)/update/available', CatalogsAvailableFormView.as_view(), name='column_available_form'),
    re_path(r'(?P<pk>[0-9]+)/update/sites', CatalogsSitesFormView.as_view(), name='column_sites_form'),
]