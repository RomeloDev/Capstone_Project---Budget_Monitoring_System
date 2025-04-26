from django.shortcuts import render

# Create your views here.
def dashboard(request):
    return render(request, 'approving_officer_app/dashboard.html')

def department_request(request):
    return render(request, 'approving_officer_app/department_request.html')

def settings(request):
    return render(request, 'approving_officer_app/settings.html')