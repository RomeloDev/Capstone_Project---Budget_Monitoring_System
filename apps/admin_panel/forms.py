# bb_budget_monitoring_system/apps/admin_panel/forms.py
from django import forms
from apps.budgets.models import DepartmentPRE
from django.core.exceptions import ValidationError


class ApprovedDocumentUploadForm(forms.ModelForm):
    """Form for uploading approved PRE documents"""
    
    class Meta:
        model = DepartmentPRE
        fields = ['approved_documents']
        widgets = {
            'approved_documents': forms.ClearableFileInput(
                attrs={
                    'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none',
                    'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx'
                }
            )
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['approved_documents'].required = True
        self.fields['approved_documents'].label = 'Upload Scanned Approved Document'
        self.fields['approved_documents'].help_text = 'Accepted formats: PDF, JPG, PNG, DOC, DOCX (Max 10MB)'
    
    def clean_approved_documents(self):
        file = self.cleaned_data.get('approved_documents')
        
        if file:
            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError('File size cannot exceed 10MB')
            
            # Check file extension
            allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
            file_ext = file.name.lower().split('.')[-1]
            if f'.{file_ext}' not in allowed_extensions:
                raise ValidationError(f'Invalid file type. Allowed: {", ".join(allowed_extensions)}')
        
        return file
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Check if PRE is in correct status
        if self.instance and self.instance.status != 'Partially Approved':
            raise ValidationError('Documents can only be uploaded for Partially Approved PREs')
        
        return cleaned_data