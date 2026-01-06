from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, Campaign, Application, Content

class UserProfileForm(forms.ModelForm):
    """Form for user profile creation and editing"""
    class Meta:
        model = UserProfile
        fields = ['user_type', 'bio', 'tiktok_handle']
        widgets = {
            'user_type': forms.Select(attrs={'class': 'form-select'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tiktok_handle': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CampaignForm(forms.ModelForm):
    """Form for creating and editing campaigns"""
    class Meta:
        model = Campaign
        fields = ['title', 'description', 'requirements', 'budget', 'status', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'budget': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ApplicationForm(forms.ModelForm):
    """Form for applying to campaigns"""
    class Meta:
        model = Application
        fields = ['proposal', 'estimated_views']
        widgets = {
            'proposal': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 5,
                'placeholder': 'Describe your approach to this campaign...'
            }),
            'estimated_views': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Estimated views for this campaign'
            }),
        }

class ContentForm(forms.ModelForm):
    """Form for adding content"""
    class Meta:
        model = Content
        fields = ['title', 'description', 'views']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'views': forms.NumberInput(attrs={'class': 'form-control'}),
        } 