from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .models import User

# Create your views here.
def admin_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
            
        admin = authenticate(request, email=email, password=password)
        
        if admin is not None and admin.is_admin:
            login(request, admin)
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
        
        if user is not None and not user.is_staff:
            login(request, user)
            return redirect('user_dashboard')
        else:
            return render(request, 'users/end_user_login.html', {'error': 'Invalid Credentials'})
    
    return render(request, 'users/end_user_login.html')

def end_user_signup(request):
    if request.method == "POST":
        # Retrieval of value in input fields
        username = request.POST.get('username')
        email = request.POST.get('email')
        department = request.POST.get('mf0_1')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm-password')
        
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
