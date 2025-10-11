def log_audit_trail(request, action, model_name, record_id=None, detail=None):
    """
    Utility function to create audit trail entries
    """
    from .models import AuditTrail
    
    AuditTrail.objects.create(
        user=request.user,
        action=action,
        model_name=model_name,
        record_id=str(record_id) if record_id else None,
        detail=detail,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
def generate_pre_number(pre):
    """
    Generate unique PRE number based on ID
    Returns: PRE-YYYY-XXXXXXXX (first 8 chars of UUID)
    """
    from datetime import datetime
    year = datetime.now().year
    return f'PRE-{year}-{str(pre.id)[:8].upper()}'