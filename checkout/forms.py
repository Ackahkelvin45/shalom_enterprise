from django import forms
from .models import Order

class OrderCancellationForm(forms.Form):
    reason = forms.ChoiceField(
        choices=Order.CANCELLATION_REASONS,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Optional additional details...',
            'rows': 3
        })
    )