from django.apps import AppConfig


class BudgetsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.budgets'
    
    def ready(self):
        # Import signals when the app is ready
        import apps.budgets.signals 
