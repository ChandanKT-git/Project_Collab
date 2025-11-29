from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.views import View
from .forms import SignupForm


class SignupView(View):
    """Handle user registration"""
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        form = SignupForm()
        return render(request, 'accounts/signup.html', {'form': form})
    
    def post(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        
        form = SignupForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                # Authenticate and login the user
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password1')
                user = authenticate(username=username, password=password)
                if user is not None:
                    login(request, user)
                    messages.success(request, f'Welcome {username}! Your account has been created successfully.')
                    return redirect('home')
                else:
                    messages.error(request, 'Account created but authentication failed. Please try logging in.')
                    return redirect('login')
            except Exception as e:
                messages.error(request, 'An error occurred during registration. Please try again.')
                # Log the error
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Registration error for username {form.cleaned_data.get("username")}: {str(e)}', exc_info=True)
        else:
            # Add user-friendly error messages
            if form.errors:
                messages.error(request, 'Please correct the errors below.')
        
        return render(request, 'accounts/signup.html', {'form': form})
