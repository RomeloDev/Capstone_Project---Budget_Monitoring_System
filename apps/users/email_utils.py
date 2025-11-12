"""
Email utility functions for user authentication
"""
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
import logging

logger = logging.getLogger('apps')


def send_password_reset_email(user, request):
    """
    Send password reset email to user with secure token link

    Args:
        user: User instance to send reset email to
        request: HttpRequest object for building absolute URLs

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Generate secure token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Build reset URL
        protocol = 'https' if request.is_secure() else 'http'
        domain = request.get_host()

        # Context for email templates
        context = {
            'user': user,
            'protocol': protocol,
            'domain': domain,
            'uid': uid,
            'token': token,
            'site_name': 'BISU Budget Monitoring System',
        }

        # Render email templates
        subject = 'Password Reset Request - BISU Budget Monitoring System'
        text_content = render_to_string('users/email/password_reset_email.txt', context)
        html_content = render_to_string('users/email/password_reset_email.html', context)

        # Create email message with both plain text and HTML versions
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL or 'noreply@bisu.edu.ph',
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")

        # Send email
        email.send(fail_silently=False)

        logger.info(f"Password reset email sent to {user.email} (User: {user.username})")
        return True

    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {str(e)}", exc_info=True)
        # Fail silently to user for security (don't reveal if email exists)
        return False
