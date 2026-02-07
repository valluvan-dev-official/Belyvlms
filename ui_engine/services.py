from django.core.cache import cache
from .models import RoleUIDefault, UIModule, UserUIPreference

class UIService:
    
    # Safety Net Defaults (Hardcoded)
    GLOBAL_DEFAULTS = {
        'dashboard': {
            "layout": "grid_default",
            "tabs": [
                {
                    "id": "overview",
                    "label": "Overview",
                    "widgets": [] 
                }
            ]
        }
    }

    def get_ui_config(self, user, role_code, module_slug):
        """
        Resolves the UI configuration for a User + Role + Module.
        
        Resolution Order:
        1. UserUIPreference (L3 - User Override)
        2. RoleUIDefault (L2 - Role Default)
        3. Global Defaults (Hardcoded Codebase Fallback)
        """
        
        # 0. Cache Check
        # Note: We must include user.id in cache key if we support user preferences
        cache_key = f"ui_config_{user.id}_{role_code}_{module_slug}"
        cached_config = cache.get(cache_key)
        # For development, we skip cache often
        # if cached_config:
        #     return cached_config

        config_data = None
        version = 1
        source = "default"

        # 1. Try Fetch User Preference (L3)
        try:
            user_pref = UserUIPreference.objects.select_related('role', 'module').get(
                user=user,
                role__code=role_code,
                module__slug=module_slug
            )
            config_data = user_pref.config
            source = "user_preference"
            # Versioning for user pref? Usually we rely on updated_at
            # But here we might just pass 1 or keep track of base version
        except UserUIPreference.DoesNotExist:
            pass

        # 2. If no User Preference, Fetch Role Default (L2)
        if not config_data:
            try:
                role_default = RoleUIDefault.objects.select_related('role', 'module').get(
                    role__code=role_code,
                    module__slug=module_slug,
                    is_active=True
                )
                config_data = role_default.config
                version = role_default.version
                source = "role_default"
            except RoleUIDefault.DoesNotExist:
                # 3. Fallback to System Global Default
                config_data = self.GLOBAL_DEFAULTS.get(module_slug, {})
                version = 1
                source = "global_fallback"

        result = {
            "config": config_data,
            "version": version,
            "source": source
        }
        
        # Cache for 5 mins
        cache.set(cache_key, result, 300)
        
        return result

    def save_user_preference(self, user, role_code, module_slug, config_data):
        """
        Saves or updates a user's UI preference.
        """
        # 1. Validate Module
        try:
            module = UIModule.objects.get(slug=module_slug)
        except UIModule.DoesNotExist:
             return {"error": "Invalid Module"}

        # 2. Get Role (We assume role_code is valid from request context)
        from rbac.models import Role
        try:
            role = Role.objects.get(code=role_code)
        except Role.DoesNotExist:
            return {"error": "Invalid Role"}

        # 3. Update or Create Preference
        obj, created = UserUIPreference.objects.update_or_create(
            user=user,
            role=role,
            module=module,
            defaults={
                'config': config_data
            }
        )
        
        # 4. Invalidate Cache
        cache_key = f"ui_config_{user.id}_{role_code}_{module_slug}"
        cache.delete(cache_key)
        
        return {"status": "success", "action": "created" if created else "updated"}
