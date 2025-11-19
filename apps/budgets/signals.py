# signals.py
from django.db.models.signals import post_save, pre_delete, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import DepartmentPRE, PurchaseRequest, ActivityDesign, SystemNotification, BudgetAllocation
from decimal import Decimal

# Track old status before save to detect status changes
@receiver(pre_save, sender=DepartmentPRE)
def track_pre_old_status(sender, instance, **kwargs):
    """Track old status before save - optimized to fetch only status field"""
    if instance.pk:
        try:
            # Optimized: only fetch 'status' field instead of entire object
            old_instance = sender.objects.only('status').get(pk=instance.pk)
            instance._old_status = old_instance.status
        except sender.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(pre_save, sender=PurchaseRequest)
def track_pr_old_status(sender, instance, **kwargs):
    """Track old status before save - optimized to fetch only status field"""
    if instance.pk:
        try:
            # Optimized: only fetch 'status' field instead of entire object
            old_instance = sender.objects.only('status').get(pk=instance.pk)
            instance._old_status = old_instance.status
        except sender.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(pre_save, sender=ActivityDesign)
def track_ad_old_status(sender, instance, **kwargs):
    """Track old status before save - optimized to fetch only status field"""
    if instance.pk:
        try:
            # Optimized: only fetch 'status' field instead of entire object
            old_instance = sender.objects.only('status').get(pk=instance.pk)
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


# ============================================================================
# BUDGET TRANSACTION LOGGING SIGNALS
# These signals create audit trail entries for all budget changes
# Wrapped in try-except to prevent failures from blocking budget operations
# ============================================================================

@receiver(post_save, sender=DepartmentPRE)
def log_pre_budget_transaction(sender, instance, created, **kwargs):
    """Log budget transaction when PRE is approved"""
    from .models import BudgetTransactionLog

    if instance.status == 'Approved' and instance.final_approved_at and not created:
        old_status = getattr(instance, '_old_status', None)

        # Only log if this is a NEW approval (status changed TO 'Approved')
        if old_status != 'Approved':
            try:
                allocation = instance.budget_allocation

                # Calculate the balance change
                amount_deducted = -instance.total_amount
                new_balance = allocation.remaining_balance
                previous_balance = new_balance - amount_deducted

                BudgetTransactionLog.objects.create(
                    allocation=allocation,
                    transaction_type='PRE_APPROVED',
                    amount_change=amount_deducted,
                    previous_balance=previous_balance,
                    new_balance=new_balance,
                    related_document_type='PRE',
                    related_document_id=str(instance.id),
                    created_by=instance.submitted_by,
                    notes=f"PRE approved for {instance.department}"
                )
            except Exception as e:
                print(f"⚠️ Failed to log PRE approval transaction: {e}")


@receiver(post_save, sender=PurchaseRequest)
def log_pr_budget_transaction(sender, instance, created, **kwargs):
    """Log budget transaction when PR is approved or rejected"""
    from .models import BudgetTransactionLog

    if not created:
        old_status = getattr(instance, '_old_status', None)

        # Log approval
        if instance.status == 'Approved' and instance.final_approved_at and old_status != 'Approved':
            try:
                allocation = instance.budget_allocation
                amount_deducted = -instance.total_amount
                new_balance = allocation.remaining_balance
                previous_balance = new_balance - amount_deducted

                BudgetTransactionLog.objects.create(
                    allocation=allocation,
                    transaction_type='PR_APPROVED',
                    amount_change=amount_deducted,
                    previous_balance=previous_balance,
                    new_balance=new_balance,
                    related_document_type='PR',
                    related_document_id=instance.pr_number or str(instance.id),
                    created_by=instance.submitted_by,
                    notes=f"Purchase Request {instance.pr_number} approved"
                )
            except Exception as e:
                print(f"⚠️ Failed to log PR approval transaction: {e}")

        # Log rejection (if previously approved - budget should be returned)
        elif instance.status == 'Rejected' and old_status == 'Approved':
            try:
                allocation = instance.budget_allocation
                amount_returned = instance.total_amount
                new_balance = allocation.remaining_balance
                previous_balance = new_balance - amount_returned

                BudgetTransactionLog.objects.create(
                    allocation=allocation,
                    transaction_type='PR_REJECTED',
                    amount_change=amount_returned,
                    previous_balance=previous_balance,
                    new_balance=new_balance,
                    related_document_type='PR',
                    related_document_id=instance.pr_number or str(instance.id),
                    created_by=instance.submitted_by,
                    notes=f"Purchase Request {instance.pr_number} rejected - budget returned"
                )
            except Exception as e:
                print(f"⚠️ Failed to log PR rejection transaction: {e}")


@receiver(post_save, sender=ActivityDesign)
def log_ad_budget_transaction(sender, instance, created, **kwargs):
    """Log budget transaction when AD is approved or rejected"""
    from .models import BudgetTransactionLog

    if not created:
        old_status = getattr(instance, '_old_status', None)

        # Log approval
        if instance.status == 'Approved' and instance.final_approved_at and old_status != 'Approved':
            try:
                allocation = instance.budget_allocation
                amount_deducted = -instance.total_amount
                new_balance = allocation.remaining_balance
                previous_balance = new_balance - amount_deducted

                BudgetTransactionLog.objects.create(
                    allocation=allocation,
                    transaction_type='AD_APPROVED',
                    amount_change=amount_deducted,
                    previous_balance=previous_balance,
                    new_balance=new_balance,
                    related_document_type='AD',
                    related_document_id=instance.ad_number or str(instance.id),
                    created_by=instance.submitted_by,
                    notes=f"Activity Design '{instance.activity_title}' approved"
                )
            except Exception as e:
                print(f"⚠️ Failed to log AD approval transaction: {e}")

        # Log rejection (if previously approved - budget should be returned)
        elif instance.status == 'Rejected' and old_status == 'Approved':
            try:
                allocation = instance.budget_allocation
                amount_returned = instance.total_amount
                new_balance = allocation.remaining_balance
                previous_balance = new_balance - amount_returned

                BudgetTransactionLog.objects.create(
                    allocation=allocation,
                    transaction_type='AD_REJECTED',
                    amount_change=amount_returned,
                    previous_balance=previous_balance,
                    new_balance=new_balance,
                    related_document_type='AD',
                    related_document_id=instance.ad_number or str(instance.id),
                    created_by=instance.submitted_by,
                    notes=f"Activity Design '{instance.activity_title}' rejected - budget returned"
                )
            except Exception as e:
                print(f"⚠️ Failed to log AD rejection transaction: {e}")


@receiver(post_save, sender=BudgetAllocation)
def log_allocation_changes(sender, instance, created, **kwargs):
    """Log budget transaction when allocation is created or modified"""
    from .models import BudgetTransactionLog

    try:
        if created:
            # Log allocation creation
            BudgetTransactionLog.objects.create(
                allocation=instance,
                transaction_type='ALLOCATION_CREATED',
                amount_change=instance.allocated_amount,
                previous_balance=Decimal('0.00'),
                new_balance=instance.remaining_balance,
                related_document_type='ALLOCATION',
                related_document_id=str(instance.id),
                created_by=None,  # Usually created by admin, can be enhanced
                notes=f"Budget allocation created for {instance.end_user.department if instance.end_user else 'N/A'}"
            )
        else:
            # Log allocation modification (if allocated_amount changed)
            # Note: This requires tracking old values, similar to status tracking
            # For now, we'll skip logging modifications to avoid complexity
            # This can be enhanced later if needed
            pass
    except Exception as e:
        print(f"⚠️ Failed to log allocation transaction: {e}")


@receiver(post_delete, sender=BudgetAllocation)
def log_allocation_deletion(sender, instance, **kwargs):
    """Log budget transaction when allocation is deleted"""
    from .models import BudgetTransactionLog

    try:
        # Create a log entry for the deletion
        # Note: Since the allocation is being deleted, we can't use FK
        # This log will exist without an allocation reference
        # We store the details in notes instead
        BudgetTransactionLog.objects.create(
            allocation=instance,  # This will be cascade deleted
            transaction_type='ALLOCATION_DELETED',
            amount_change=-instance.remaining_balance,
            previous_balance=instance.remaining_balance,
            new_balance=Decimal('0.00'),
            related_document_type='ALLOCATION',
            related_document_id=str(instance.id),
            created_by=None,
            notes=f"Budget allocation deleted for {instance.end_user.department if instance.end_user else 'N/A'}"
        )
    except Exception as e:
        print(f"⚠️ Failed to log allocation deletion: {e}")


# ============================================================================
# APPROVAL REVERSAL HANDLERS (GAP #3 FIX)
# These signals return budget when approval status is reversed
# ============================================================================

@receiver(post_save, sender=PurchaseRequest)
def handle_pr_approval_reversal(sender, instance, created, **kwargs):
    """
    Return budget when PR approval is reversed (status changes FROM 'Approved' TO other status)
    This fixes GAP #3: No Budget Reversal Process
    """
    if not created:
        old_status = getattr(instance, '_old_status', None)

        # Check if status changed FROM 'Approved' TO something else
        if old_status == 'Approved' and instance.status != 'Approved':
            try:
                allocation = instance.budget_allocation

                print(f"\n🔄 PR Approval Reversed: {instance.pr_number}")
                print(f"   Status changed: Approved → {instance.status}")
                print(f"   Returning budget: ₱{instance.total_amount:,.2f}")

                # Return the budget
                allocation.pr_amount_used -= instance.total_amount

                # Ensure it doesn't go negative
                if allocation.pr_amount_used < 0:
                    allocation.pr_amount_used = Decimal('0.00')

                allocation.update_remaining_balance()

                print(f"✅ Budget returned successfully")
                print(f"   New pr_amount_used: ₱{allocation.pr_amount_used:,.2f}")
                print(f"   New remaining_balance: ₱{allocation.remaining_balance:,.2f}\n")

                # Log the reversal transaction
                from .models import BudgetTransactionLog
                BudgetTransactionLog.objects.create(
                    allocation=allocation,
                    transaction_type='PR_REJECTED',  # Reuse existing type
                    amount_change=instance.total_amount,  # Positive (budget returned)
                    previous_balance=allocation.remaining_balance - instance.total_amount,
                    new_balance=allocation.remaining_balance,
                    related_document_type='PR',
                    related_document_id=instance.pr_number or str(instance.id),
                    created_by=instance.submitted_by,
                    notes=f"PR approval reversed - status changed to {instance.status}"
                )

                # Notify user
                from .models import SystemNotification
                SystemNotification.objects.create(
                    recipient=instance.submitted_by,
                    title=f"PR Approval Reversed",
                    message=f"The approval for PR {instance.pr_number} has been reversed. Budget of ₱{instance.total_amount:,.2f} has been returned.",
                    content_type='pr',
                    object_id=instance.id
                )

            except Exception as e:
                print(f"⚠️ Error returning budget for reversed PR: {e}")


@receiver(post_save, sender=ActivityDesign)
def handle_ad_approval_reversal(sender, instance, created, **kwargs):
    """
    Return budget when AD approval is reversed (status changes FROM 'Approved' TO other status)
    This fixes GAP #3: No Budget Reversal Process
    """
    if not created:
        old_status = getattr(instance, '_old_status', None)

        # Check if status changed FROM 'Approved' TO something else
        if old_status == 'Approved' and instance.status != 'Approved':
            try:
                allocation = instance.budget_allocation

                print(f"\n🔄 AD Approval Reversed: {instance.ad_number or instance.id.hex[:8]}")
                print(f"   Status changed: Approved → {instance.status}")
                print(f"   Returning budget: ₱{instance.total_amount:,.2f}")

                # Return the budget
                allocation.ad_amount_used -= instance.total_amount

                # Ensure it doesn't go negative
                if allocation.ad_amount_used < 0:
                    allocation.ad_amount_used = Decimal('0.00')

                allocation.update_remaining_balance()

                print(f"✅ Budget returned successfully")
                print(f"   New ad_amount_used: ₱{allocation.ad_amount_used:,.2f}")
                print(f"   New remaining_balance: ₱{allocation.remaining_balance:,.2f}\n")

                # Log the reversal transaction
                from .models import BudgetTransactionLog
                BudgetTransactionLog.objects.create(
                    allocation=allocation,
                    transaction_type='AD_REJECTED',  # Reuse existing type
                    amount_change=instance.total_amount,  # Positive (budget returned)
                    previous_balance=allocation.remaining_balance - instance.total_amount,
                    new_balance=allocation.remaining_balance,
                    related_document_type='AD',
                    related_document_id=instance.ad_number or str(instance.id),
                    created_by=instance.submitted_by,
                    notes=f"AD approval reversed - status changed to {instance.status}"
                )

                # Notify user
                from .models import SystemNotification
                SystemNotification.objects.create(
                    recipient=instance.submitted_by,
                    title=f"AD Approval Reversed",
                    message=f"The approval for AD '{instance.activity_title}' has been reversed. Budget of ₱{instance.total_amount:,.2f} has been returned.",
                    content_type='ad',
                    object_id=instance.id
                )

            except Exception as e:
                print(f"⚠️ Error returning budget for reversed AD: {e}")