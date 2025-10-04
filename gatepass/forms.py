from django import forms
from django.contrib.auth import get_user_model
from .models import GatePass, GatePassPermission, GATE_PASS_TYPE_CHOICES, GATE_PASS_STATUS_CHOICES

User = get_user_model()

class GatePassForm(forms.ModelForm):
    class Meta:
        model = GatePass
        fields = [
            'visitor_name', 'visitor_phone', 'visitor_email', 'visitor_id_proof',
            'company_organization', 'pass_type', 'purpose', 'valid_from', 'valid_until',
            'authorized_areas', 'escort_required', 'escort_name', 'escort_phone', 'notes'
        ]
        widgets = {
            'visitor_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Visitor Name', 'required': True}),
            'visitor_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number', 'required': True}),
            'visitor_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'visitor_id_proof': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ID Proof Number', 'required': True}),
            'company_organization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company/Organization'}),
            'pass_type': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'purpose': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Purpose of visit', 'required': True}),
            'valid_from': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local', 'required': True}),
            'valid_until': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local', 'required': True}),
            'authorized_areas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Authorized areas (optional)'}),
            'escort_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'escort_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escort Name'}),
            'escort_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escort Phone'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes (optional)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['visitor_email'].required = False
        self.fields['company_organization'].required = False
        self.fields['authorized_areas'].required = False
        self.fields['escort_name'].required = False
        self.fields['escort_phone'].required = False
        self.fields['notes'].required = False

class GatePassStatusUpdateForm(forms.ModelForm):
    class Meta:
        model = GatePass
        fields = ['status', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Add notes about status change'}),
        }

class GatePassPermissionForm(forms.ModelForm):
    class Meta:
        model = GatePassPermission
        fields = ['user', 'can_create_gatepass']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'can_create_gatepass': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.filter(
            user_type__in=['MEMBER', 'VOLUNTEER', 'COORDINATOR']
        ).exclude(
            user_type='ADMINISTRATOR'
        )
        self.fields['user'].empty_label = "Select User"

class GatePassSearchForm(forms.Form):
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by pass number, visitor name, or phone'
        })
    )
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + GATE_PASS_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    pass_type = forms.ChoiceField(
        choices=[('', 'All Types')] + GATE_PASS_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )