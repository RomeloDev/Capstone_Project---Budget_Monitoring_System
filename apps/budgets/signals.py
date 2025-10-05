# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import DepartmentPRE, PurchaseRequest, ActivityDesign, SystemNotification

@receiver(post_save, sender=DepartmentPRE)
def update_budget_on_pre_approval(sender, instance, created, **kwargs):
    """Update budget allocation when PRE is finally approved"""
    if instance.status == 'Approved' and instance.final_approved_at:
        # Check if this is a status change to 'Approved' (not just an update)
        if not created:  # Only for updates, not new creations
            allocation = instance.budget_allocation
            
            # Only update if this amount hasn't been deducted yet
            if allocation.pre_amount_used < instance.total_amount:
                allocation.pre_amount_used = instance.total_amount
                allocation.update_remaining_balance()
                
                # Create notification for user
                SystemNotification.objects.create(
                    recipient=instance.submitted_by,
                    title=f"PRE Finally Approved",
                    message=f"Your PRE for {instance.department} has been finally approved. Amount: ₱{instance.total_amount:,.2f}",
                    content_type='pre',
                    object_id=instance.id
                )

@receiver(post_save, sender=PurchaseRequest)
def update_budget_on_pr_approval(sender, instance, created, **kwargs):
    """Update budget allocation when PR is finally approved"""
    if instance.status == 'Approved' and instance.final_approved_at:
        if not created:
            allocation = instance.budget_allocation
            
            if allocation.pr_amount_used < instance.total_amount:
                allocation.pr_amount_used = instance.total_amount
                allocation.update_remaining_balance()
                
                # Create notification for user
                SystemNotification.objects.create(
                    recipient=instance.submitted_by,
                    title=f"Purchase Request Finally Approved",
                    message=f"Your Purchase Request has been finally approved. Amount: ₱{instance.total_amount:,.2f}",
                    content_type='pr',
                    object_id=instance.id
                )

@receiver(post_save, sender=ActivityDesign)
def update_budget_on_ad_approval(sender, instance, created, **kwargs):
    """Update budget allocation when AD is finally approved"""
    if instance.status == 'Approved' and instance.final_approved_at:
        if not created:
            allocation = instance.budget_allocation
            
            if allocation.ad_amount_used < instance.total_amount:
                allocation.ad_amount_used = instance.total_amount
                allocation.update_remaining_balance()
                
                # Create notification for user
                SystemNotification.objects.create(
                    recipient=instance.submitted_by,
                    title=f"Activity Design Finally Approved",
                    message=f"Your Activity Design '{instance.activity_title}' has been finally approved. Amount: ₱{instance.total_amount:,.2f}",
                    content_type='ad',
                    object_id=instance.id
                )

@receiver(post_save, sender=DepartmentPRE)
def notify_pre_status_change(sender, instance, created, **kwargs):
    """Notify user when PRE status changes"""
    if not created:  # Only for updates
        status_messages = {
            'Pending': 'Your PRE has been submitted and is pending review.',
            'Partially Approved': 'Your PRE has been partially approved. You can now download the PDF to print and sign.',
            'Rejected': 'Your PRE has been rejected. Please check the admin notes for details.',
        }
        
        if instance.status in status_messages:
            SystemNotification.objects.create(
                recipient=instance.submitted_by,
                title=f"PRE Status Updated: {instance.status}",
                message=status_messages[instance.status],
                content_type='pre',
                object_id=instance.id
            )

@receiver(post_save, sender=PurchaseRequest)
def notify_pr_status_change(sender, instance, created, **kwargs):
    """Notify user when PR status changes"""
    if not created:
        status_messages = {
            'Pending': 'Your Purchase Request has been submitted and is pending review.',
            'Partially Approved': 'Your Purchase Request has been partially approved. You can now download the PDF to print and sign.',
            'Rejected': 'Your Purchase Request has been rejected. Please check the admin notes for details.',
        }
        
        if instance.status in status_messages:
            SystemNotification.objects.create(
                recipient=instance.submitted_by,
                title=f"Purchase Request Status Updated: {instance.status}",
                message=status_messages[instance.status],
                content_type='pr',
                object_id=instance.id
            )

@receiver(post_save, sender=ActivityDesign)
def notify_ad_status_change(sender, instance, created, **kwargs):
    """Notify user when AD status changes"""
    if not created:
        status_messages = {
            'Pending': 'Your Activity Design has been submitted and is pending review.',
            'Partially Approved': 'Your Activity Design has been partially approved. You can now download the PDF to print and sign.',
            'Rejected': 'Your Activity Design has been rejected. Please check the admin notes for details.',
        }
        
        if instance.status in status_messages:
            SystemNotification.objects.create(
                recipient=instance.submitted_by,
                title=f"Activity Design Status Updated: {instance.status}",
                message=status_messages[instance.status],
                content_type='ad',
                object_id=instance.id
            )