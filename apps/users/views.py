from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from .models import User
from apps.admin_panel.utils import log_audit_trail
from .forms import PasswordResetRequestForm, SetPasswordForm
from .email_utils import send_password_reset_email
import logging

logger = logging.getLogger('apps')

# Create your views here.
def admin_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
            
        admin = authenticate(request, email=email, password=password)
        
        if admin is not None and admin.is_admin:
            login(request, admin)
            log_audit_trail(
                request=request,
                action='LOGIN',
                model_name='User',
                detail=f'User {admin.username} logged in as admin',
            )
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Invalid credentials or not admin")
        
    return render(request, 'users/admin_login.html')

def end_user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user_obj = User.objects.get(email=email)
            print(f"User exists: {user_obj.email}, Hashed Password: {user_obj.password}")
        except User.DoesNotExist:
            print("User does not exist")
            
        user = authenticate(request, email=email, password=password)
        
        if user is not None and not user.is_staff and not user.is_approving_officer:
            login(request, user)
            log_audit_trail(
                request=request,
                action='LOGIN',
                model_name='User',
                detail=f'User {user.username} logged in as end user',
            )
            return redirect('user_dashboard')
        elif user is not None and user.is_approving_officer:
            login(request, user)
            log_audit_trail(
                request=request,
                action='LOGIN',
                model_name='User',
                detail=f'User {user.username} logged in as approving officer',
            )
            return redirect('approving_officer_dashboard')
        else:
            return render(request, 'users/end_user_login.html', {'error': 'Invalid Credentials'})
    
    return render(request, 'users/end_user_login.html')

def end_user_signup(request):
    if request.method == "POST":
        # Retrieval of value in input fields
        username = request.POST.get('username')
        email = request.POST.get('email')
        department = request.POST.get('mfo_1')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm-password')
        department_head = request.POST.get('department') # This is for future changes. Add a logic about this
        
        # Validate password confirmation
        if password != confirm_password:
            return render(request, 'users/end_user_signup.html', {'error': 'Passwords do not match'})
        
        # Check if the department or username or email are already exists
        if User.objects.filter(username=username).exists():
            return render(request, 'users/end_user_signup.html', {'error': 'Username already taken.'})

        if User.objects.filter(email=email).exists():
            return render(request, 'users/end_user_signup.html', {'error': f'Email {email} already registered.'})
        
        if User.objects.filter(department=department).exists():
            return render(request, 'users/end_user_signup.html', {'error': f'Department {department} already registered.'})
        
        # Create and save the user
        user = User.objects.create_user(username=username, email=email, password=password, department=department)
        login(request, user)
        return redirect('user_dashboard')

    return render(request, 'users/end_user_signup.html')


# ============================================================================
# PASSWORD RESET VIEWS
# ============================================================================

def password_reset_request(request):
    """
    View for requesting password reset via email
    User enters email, system sends reset link
    """
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']

            # Try to find user with this email
            try:
                user = User.objects.get(email=email, is_active=True, is_archived=False)

                # Send reset email
                send_password_reset_email(user, request)

                # Log audit trail
                log_audit_trail(
                    request=request,
                    action='PASSWORD_RESET_REQUEST',
                    model_name='User',
                    detail=f'Password reset requested for {user.username}',
                )

                logger.info(f"Password reset requested for user: {user.username} ({user.email})")

            except User.DoesNotExist:
                # Don't reveal that user doesn't exist (security best practice)
                logger.warning(f"Password reset attempted for non-existent/inactive email: {email}")
                pass

            # Always redirect to "sent" page regardless of email existence
            return redirect('password_reset_sent')
    else:
        form = PasswordResetRequestForm()

    # Determine which base template to use
    next_page = request.GET.get('next', 'user')
    if next_page == 'admin':
        base_template = 'admin_base_template/admin_auth.html'
    else:
        base_template = 'end_user_base_template/end_user_auth.html'

    return render(request, 'users/password_reset_request.html', {
        'form': form,
        'base_template': base_template,
    })


def password_reset_sent(request):
    """
    Confirmation page after requesting password reset
    Shows 'Check your email' message
    """
    return render(request, 'users/password_reset_sent.html')


def password_reset_confirm(request, uidb64, token):
    """
    View for confirming password reset and setting new password
    Validates token and allows user to set new password
    """
    try:
        # Decode user ID from URL
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    # Validate token
    if user is not None and default_token_generator.check_token(user, token):
        # Check if user is still active and not archived
        if not user.is_active or user.is_archived:
            messages.error(request, "This account is no longer active.")
            logger.warning(f"Password reset attempted for inactive/archived user: {user.username}")
            return redirect('end_user_login')

        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                # Save new password
                form.save()

                # Log audit trail
                log_audit_trail(
                    request=request,
                    action='PASSWORD_RESET_COMPLETE',
                    model_name='User',
                    detail=f'Password successfully reset for {user.username}',
                )

                logger.info(f"Password successfully reset for user: {user.username}")

                messages.success(request, "Your password has been reset successfully! Please log in with your new password.")
                return redirect('password_reset_complete')
        else:
            form = SetPasswordForm(user)

        return render(request, 'users/password_reset_confirm.html', {
            'form': form,
            'validlink': True,
        })
    else:
        # Invalid or expired token
        logger.warning(f"Invalid/expired password reset token used for uidb64: {uidb64}")
        messages.error(request, "This password reset link is invalid or has expired.")
        return render(request, 'users/password_reset_confirm.html', {
            'validlink': False,
        })


def password_reset_complete(request):
    """
    Success page after password reset
    Shows success message with links to login
    """
    return render(request, 'users/password_reset_complete.html')

