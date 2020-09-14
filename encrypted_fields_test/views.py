from django.views.generic import ListView, CreateView, UpdateView

from .models import DemoModel
from .forms import DemoModelForm


class DemoListView(ListView):
    model = DemoModel


class DemoCreateView(CreateView):
    model = DemoModel
    form_class = DemoModelForm


class DemoUpdateView(UpdateView):
    model = DemoModel
    form_class = DemoModelForm
    template_name_suffix = "_update_form"
