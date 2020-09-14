from django.forms import ModelForm, TextInput

from .models import DemoModel


class DemoModelForm(ModelForm):
    class Meta:
        model = DemoModel
        fields = ["name", "email", "date", "date_2", "number", "text"]
        labels = {
            "text": "Overridden Text label in ModelForm",
        }
        help_texts = {
            "text": "The help text and widget have been overridden in ModelForm.",
        }
        widgets = {
            "text": TextInput(
                attrs={"size": 20, "title": "This is no longer a Text Area!"}
            ),
        }
