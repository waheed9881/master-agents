from django import forms

from apps.knowledge.models import KnowledgeSourceType


class KnowledgeSourceForm(forms.Form):
    title = forms.CharField(max_length=255)
    content = forms.CharField(widget=forms.Textarea(attrs={"rows": 8}))
    source_type = forms.ChoiceField(choices=KnowledgeSourceType.choices, initial=KnowledgeSourceType.TEXT)
    agent_instance_id = forms.IntegerField(required=False)
