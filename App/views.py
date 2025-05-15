from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User, auth
from .models import GeminiChatHistory
import json
from django.http import JsonResponse
from django.conf import settings
import os
from django.views.decorators.csrf import csrf_exempt
import speech_recognition as sr
from pydub import AudioSegment
import io
import tempfile

from .search_chunks import search_textbook
from .gemini_api import ask_gemini

def register(request):
    if request.method == 'POST':
        username = request.POST['username'].strip()
        email = request.POST['email'].strip()
        password = request.POST['password'].strip()
        password2 = request.POST['password2'].strip()
        
        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email Already Exists')
            elif User.objects.filter(username=username).exists():
                messages.error(request, 'Username Already Exists')
            else:
                # Create user using Django's create_user method
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )
                user.save()
                messages.success(request, 'Successfully Registered')
                return redirect('login')
        else:
            messages.error(request, 'Password does not match')

    return render(request, 'register.html')

def login(request):
    """User login view"""
    if request.method == 'POST':
        email = request.POST['email'].strip()
        password = request.POST['password'].strip()
        
        # Authenticate user
        user = auth.authenticate(username=email, password=password)
        
        if user is not None:
            auth.login(request, user)
            messages.success(request, f"Successfully logged in as {user}")
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid Credentials')
            return redirect('login')
        
    return render(request, 'login.html')

def logout(request):
    auth.logout(request)
    return redirect('login')
 
@login_required(login_url='login') 
def index(request):
    return render(request, 'index.html')

@login_required(login_url='login')
def dashboard(request):
    return render(request, 'dashboard.html')

@login_required(login_url='login')
def chat(request):  
    user_obj = request.user 
    chat_history = GeminiChatHistory.objects.filter(user=user_obj, role = 'user').order_by('timestamp')[:7]
    context= {
        'chat_history':chat_history
    }
    return render(request, 'chat.html', context)


@login_required
def get_chat_history(request):
    user_obj = request.user
    chat_history = GeminiChatHistory.objects.filter(user=user_obj).order_by('timestamp')
    
    data = [
        {
            'role': 'user' if msg.role == 'user' else 'ai',  # Convert 'model' to 'ai' for frontend
            'message': msg.message,
            'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M')
        }
        for msg in chat_history
    ]
    
    return JsonResponse({'chat_history': data})

@login_required(login_url='login')
def chat_history(request):
    return render(request, 'chatHistory.html')

@csrf_exempt
def diagnose(request):
    """API endpoint to process user symptoms and return medical advice"""
    if request.method == 'POST':
        try:
            # Parse JSON data from request body
            data = json.loads(request.body)
            user_symptoms = data.get('symptoms', '')
            
            if not user_symptoms:
                return JsonResponse({'error': 'No symptoms provided.'}, status=400)
            
            # 1. Search textbook chunks for relevant medical information
            context_texts = search_textbook(user_symptoms)
            
            # 2. Generate response with Gemini AI
            answer = ask_gemini(user_symptoms, context_texts, request.user)
            
            # 3. Return formatted response
            return JsonResponse({'answer': answer})
        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format.'}, status=400)
        except Exception as e:
            import traceback
            print(f"Error in diagnose view: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Only POST requests are accepted.'}, status=405)

def convert_voice_to_text(audio_file):
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
        # Write the uploaded file to the temporary file
        for chunk in audio_file.chunks():
            temp_file.write(chunk)
        temp_file.flush()
        
        # Convert to text using speech recognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_file.name) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)
        
        # Clean up the temporary file
        os.unlink(temp_file.name)
        
        return text

@login_required
def settings(request):
    if request.method == 'POST':
        user = request.user
        user.username = request.POST['username']
        user.email = request.POST['email']
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')

        # Update profile picture and bio
        # Note: Make sure you have a Profile model related to User
        try:
            profile = user.profile
            profile.bio = request.POST.get('bio', '')
            if 'profile_picture' in request.FILES:
                profile.profile_picture = request.FILES['profile_picture']
            profile.save()
        except AttributeError:
            # Handle case where profile doesn't exist
            pass

        user.save()
        messages.success(request, 'Settings updated successfully')
        return redirect('settings')

    return render(request, 'settings.html')
 