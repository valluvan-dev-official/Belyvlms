from django import forms
from django.contrib import admin
from .models import RolePermission, Permission, Role

class RoleForm(forms.ModelForm):
    """
    Form for RoleAdmin to manage permissions directly.
    """
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        required=False,
        widget=admin.widgets.FilteredSelectMultiple('Permissions', is_stacked=False),
        help_text="Manage all permissions for this role in one place."
    )

    class Meta:
        model = Role
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Load all existing permissions for this role
            self.fields['permissions'].initial = Permission.objects.filter(
                role_permissions__role=self.instance
            )

    def save(self, commit=True):
        role = super().save(commit=False)
        if commit:
            role.save()
        
        if role.pk:
            # Sync permissions
            new_permissions = self.cleaned_data['permissions']
            
            # 1. Get current permissions
            current_permissions = set(Permission.objects.filter(role_permissions__role=role))
            new_permissions_set = set(new_permissions)
            
            # 2. Determine what to add and remove
            to_add = new_permissions_set - current_permissions
            to_remove = current_permissions - new_permissions_set
            
            # 3. Add new
            for perm in to_add:
                RolePermission.objects.create(role=role, permission=perm)
                
            # 4. Remove old
            RolePermission.objects.filter(role=role, permission__in=to_remove).delete()
            
        return role

class RolePermissionForm(forms.ModelForm):
    """
    Custom form to allow selecting MULTIPLE permissions for a single Role.
    """
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        required=True,
        widget=admin.widgets.FilteredSelectMultiple('Permissions', is_stacked=False),
        help_text="Select multiple permissions to assign to this role."
    )

    class Meta:
        model = RolePermission
        fields = ('role', 'permissions')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Edit Mode: Pre-select ALL existing permissions for this role
            # This makes the form behave like a "Role Editor" even when accessed via a single permission link
            self.fields['permissions'].initial = Permission.objects.filter(
                role_permissions__role=self.instance.role
            )
            # Also lock the 'role' field so they don't accidentally switch roles while editing permissions
            self.fields['role'].disabled = True

    def save(self, commit=True):
        # We don't save normally because we need to create multiple objects.
        # We will handle the saving in the Admin's save_model method or here if we trick it.
        # But `save_model` is cleaner.
        # Let's just return the instance without committing here, and handle the rest in Admin.
        return super().save(commit=False)
