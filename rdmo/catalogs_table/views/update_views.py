import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.models import Site
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy
from django.views.generic import UpdateView
from django.shortcuts import render

from rdmo.core.views import ModelPermissionMixin
from rdmo.questions.models import Catalog


class HTMXResponse(HttpResponse):
    ''' adds the HTMX headers to a HttpRepsonse '''

    def __init__(self,
                    status=204,
                    trigger_name=None,
                    trigger_val=None,
                    message=None,
                    redirect=None,
                    refresh=None,
                    location=None
                    ):
        super().__init__(status=status)
        hx_trigger = {}
        if trigger_name:
            hx_trigger.update({trigger_name: trigger_val})
        if message:
            hx_trigger.update({"showMessage": message})
        
        if hx_trigger:
            self.headers['HX-Trigger'] = json.dumps(hx_trigger)
        if redirect:
            self.headers['HX-Redirect'] = json.dumps(redirect)
        if refresh:
            self.headers['HX-Refresh'] = "true"
        if location:
            self.headers['HX-Location'] = json.dumps(location)


class CatalogsLockedFormView(ModelPermissionMixin, LoginRequiredMixin, UpdateView):
    permission_required = 'questions.view_catalog'
    model = Catalog
    fields = ('locked',)
    template_name = 'catalogs_table/columns/locked_form.html'
    success_url = reverse_lazy('column_locked_list')

    def form_valid(self, form):
        form.save()
        msg = f'{self.get_object().title} changed to {form.cleaned_data.get("locked")}'
        pk =  str(self.get_object().pk)
        trigger = f'lockedChanged-{pk}'
        return HTMXResponse(trigger_name=trigger, message=msg)

class CatalogsAvailableFormView(ModelPermissionMixin, LoginRequiredMixin, UpdateView):
    permission_required = 'questions.view_catalog'
    model = Catalog
    fields = ('available',)
    template_name = 'catalogs_table/columns/available_form.html'
    success_url = reverse_lazy('column_available_list')
    
    def form_valid(self, form):
        if form.has_changed() and self.object.locked:
            pass # Perhaps raise a validation error here
        form.save()
        msg = f'{self.get_object().title} changed to {form.cleaned_data.get("available")}'
        pk =  str(self.get_object().pk)
        trigger = f'availableChanged-{pk}'
        return HTMXResponse(trigger_name=trigger, message=msg)


class CatalogsSitesFormView(ModelPermissionMixin, LoginRequiredMixin, UpdateView):
    permission_required = 'questions.view_catalog'
    model = Catalog
    fields = ('sites',)
    template_name = 'catalogs_table/columns/sites_form.html'

    def get_success_url(self) -> str:
        return reverse_lazy('column_sites_list', args=str(self.get_object().pk))

    def get_context_data(self, **kwargs):
        redirect_url = self.get_success_url()
        kwargs.update({
                       'redirect_url' : redirect_url, 
                       'pk' : str(self.get_object().pk)
                    })
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
    
        form.save()
        context = {
                'sites': form.cleaned_data['sites'].values(),
                'all_sites' : Site.objects.count() == form.cleaned_data['sites'].values().count(),
                'sites_form_url' : reverse_lazy('column_sites_form', args=str(self.get_object().pk)),
                'sites_list_url' : reverse_lazy('column_sites_list', args=str(self.get_object().pk)),
                'pk' : str(self.get_object().pk)
                }
        return render(self.request, 'catalogs_table/columns/sites.html', context=context)
