# signals.py
from django.db.models.signals import post_save, pre_delete, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import DepartmentPRE, PurchaseRequest, ActivityDesign, SystemNotification, BudgetAllocation
from decimal import Decimal

# Track old status before save to detect status changes
@receiver(pre_save, sender=DepartmentPRE)
def track_pre_old_status(sender, instance, **kwargs):
    """Track old status before save"""
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except sender.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(pre_save, sender=PurchaseRequest)
def track_pr_old_status(sender, instance, **kwargs):
    """Track old status before save"""
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except sender.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(pre_save, sender=ActivityDesign)
def track_ad_old_status(sender, instance, **kwargs):
    """Track old status before save"""
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except sender.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(post_save, sender=DepartmentPRE)
def update_budget_on_pre_approval(sender, instance, created, **kwargs):
    """Update budget allocation when PRE is finally approved"""
    if instance.status == 'Approved' and instance.final_approved_at:
        # Check if this is a status change to 'Approved' (not just an update)
        if not created:  # Only for updates, not new creations
            allocation = instance.budget_allocation

            # Check if status changed FROM something else TO 'Approved'
            old_status = getattr(instance, '_old_status', None)
            if old_status != 'Approved':
                # This is a NEW approval, add the amount
                allocation.pre_amount_used += instance.total_amount
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

            # Check if status changed FROM something else TO 'Approved'
            old_status = getattr(instance, '_old_status', None)
            if old_status != 'Approved':
                # Validate before adding (safety check - should already be validated in view)
                validation_errors = instance.validate_against_budget()
                if validation_errors:
                    print(f"⚠️  WARNING: PR {instance.pr_number} approved but has budget errors:")
                    for error in validation_errors:
                        print(f"   - {error}")

                # This is a NEW approval, add the amount
                allocation.pr_amount_used += instance.total_amount
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

            # Check if status changed FROM something else TO 'Approved'
            old_status = getattr(instance, '_old_status', None)
            if old_status != 'Approved':
                # Validate before adding (safety check - should already be validated in view)
                validation_errors = instance.validate_against_budget()
                if validation_errors:
                    print(f"⚠️  WARNING: AD {instance.ad_number or instance.id.hex[:8]} approved but has budget errors:")
                    for error in validation_errors:
                        print(f"   - {error}")

                # This is a NEW approval, add the amount
                allocation.ad_amount_used += instance.total_amount
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
            
@receiver(pre_delete, sender=BudgetAllocation)
def return_budget_on_allocation_delete(sender, instance, **kwargs):
    """
    Return allocated budget to ApprovedBudget when BudgetAllocation is deleted.
    This runs BEFORE the allocation is deleted, so we can still access its data.
    """
    if instance.approved_budget:
        # Calculate how much budget to return
        # Only return the unused portion
        used_amount = instance.get_total_used()
        unused_amount = instance.allocated_amount - used_amount
        
        print(f"\n{'='*60}")
        print(f"🗑️ Deleting BudgetAllocation: {instance.department}")
        print(f"   Allocated Amount: ₱{instance.allocated_amount:,.2f}")
        print(f"   Used Amount: ₱{used_amount:,.2f}")
        print(f"   Unused Amount: ₱{unused_amount:,.2f}")
        print(f"{'='*60}\n")
        
        # Return unused budget to ApprovedBudget
        approved_budget = instance.approved_budget
        approved_budget.remaining_budget += unused_amount
        approved_budget.save()
        
        print(f"✅ Returned ₱{unused_amount:,.2f} to {approved_budget.title}")
        print(f"   New remaining_budget: ₱{approved_budget.remaining_budget:,.2f}\n")


@receiver(pre_delete, sender=DepartmentPRE)
def return_pre_budget_on_delete(sender, instance, **kwargs):
    """
    Return PRE budget to BudgetAllocation when PRE is deleted.
    Only if the PRE was approved (budget was deducted).
    """
    if instance.status == 'Approved' and instance.budget_allocation:
        # Calculate correct total from line items
        correct_total = sum(item.get_total() for item in instance.line_items.all())
        
        print(f"\n🗑️ Deleting Approved PRE: {instance.department}")
        print(f"   PRE Total: ₱{correct_total:,.2f}")
        
        # Return budget to allocation
        allocation = instance.budget_allocation
        allocation.pre_amount_used -= correct_total
        
        # Ensure it doesn't go negative
        if allocation.pre_amount_used < 0:
            allocation.pre_amount_used = Decimal('0.00')
        
        allocation.update_remaining_balance()
        
        print(f"✅ Returned ₱{correct_total:,.2f} to allocation")
        print(f"   New pre_amount_used: ₱{allocation.pre_amount_used:,.2f}")
        print(f"   New remaining_balance: ₱{allocation.remaining_balance:,.2f}\n")


@receiver(pre_delete, sender=PurchaseRequest)
def return_pr_budget_on_delete(sender, instance, **kwargs):
    """
    Return PR budget to BudgetAllocation when PR is deleted.
    Only if the PR was approved (budget was deducted).
    """
    if instance.status == 'Approved' and instance.budget_allocation:
        print(f"\n🗑️ Deleting Approved PR: {instance.pr_number}")
        print(f"   PR Total: ₱{instance.total_amount:,.2f}")
        
        # Return budget to allocation
        allocation = instance.budget_allocation
        allocation.pr_amount_used -= instance.total_amount
        
        # Ensure it doesn't go negative
        if allocation.pr_amount_used < 0:
            allocation.pr_amount_used = Decimal('0.00')
        
        allocation.update_remaining_balance()
        
        print(f"✅ Returned ₱{instance.total_amount:,.2f} to allocation")
        print(f"   New pr_amount_used: ₱{allocation.pr_amount_used:,.2f}")
        print(f"   New remaining_balance: ₱{allocation.remaining_balance:,.2f}\n")


@receiver(pre_delete, sender=ActivityDesign)
def return_ad_budget_on_delete(sender, instance, **kwargs):
    """
    Return AD budget to BudgetAllocation when AD is deleted.
    Only if the AD was approved (budget was deducted).
    """
    if instance.status == 'Approved' and instance.budget_allocation:
        print(f"\n🗑️ Deleting Approved AD: {instance.activity_title}")
        print(f"   AD Total: ₱{instance.total_amount:,.2f}")
        
        # Return budget to allocation
        allocation = instance.budget_allocation
        allocation.ad_amount_used -= instance.total_amount
        
        # Ensure it doesn't go negative
        if allocation.ad_amount_used < 0:
            allocation.ad_amount_used = Decimal('0.00')
        
        allocation.update_remaining_balance()
        
        print(f"✅ Returned ₱{instance.total_amount:,.2f} to allocation")
        print(f"   New ad_amount_used: ₱{allocation.ad_amount_used:,.2f}")
        print(f"   New remaining_balance: ₱{allocation.remaining_balance:,.2f}\n")