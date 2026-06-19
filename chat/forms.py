from django import forms
from .models import Message

class ChatMessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content', 'image', 'image_type']

    def clean(self):
        cleaned_data = super().clean()
        content = cleaned_data.get('content')
        image = cleaned_data.get('image')
        if not content and not image:
            raise forms.ValidationError('Debe proporcionar un mensaje o una imagen.')
        return cleaned_data
