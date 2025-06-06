from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User, auth
from .models import GeminiChatHistory, Profile, VoiceNote, MedicationRecommendation, ChatImage
import json
from django.http import JsonResponse, HttpResponse
from django.conf import settings
import os
import tempfile
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from datetime import datetime
from django.utils import timezone
from io import BytesIO
import re
import speech_recognition as sr
from pydub import AudioSegment
from pydub.utils import make_chunks
import requests
from .search_chunks import search_textbook
from .gemini_api import ask_gemini
from xhtml2pdf import pisa

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
    return redirect('/')
 
 
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
            'role': 'user' if msg.role == 'user' else 'ai',
            'message': msg.message,
            'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M'),
            'voice_note': {
                'url': msg.voice_note.audio_file.url,
                'transcribed_text': msg.voice_note.transcribed_text
            } if msg.voice_note else None,
            'images': [{
                'url': request.build_absolute_uri(img.image.url),
                'id': img.id
            } for img in ChatImage.objects.filter(chat_history=msg)]
        }
        for msg in chat_history
    ]
    
    return JsonResponse({
        'chat_history': data,
        'total_messages': len(data)
    })

@login_required(login_url='login')
def chat_history(request):
    user_obj = request.user 
    chat_history = GeminiChatHistory.objects.filter(user=user_obj, role = 'user').order_by('timestamp')[:7]
    context= {
        'chat_history':chat_history
    }
    return render(request, 'chatHistory.html', context)


@csrf_exempt
def diagnose(request):
    """API endpoint to process user symptoms and return medical advice"""
    if request.method == 'POST':
        try:
            # Handle JSON data (assume text input)
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                # This part will be moved to a new view or handled differently
                # For now, we return an error as this view will only handle voice notes or be removed
                return JsonResponse({'error': 'This endpoint is for voice note transcription only.'}, status=400)

            # Handle form data with voice note
            elif 'voice_note' in request.FILES:
                voice_note = request.FILES['voice_note']
                if not voice_note.name.endswith('.wav'):
                    return JsonResponse({'error': 'Only WAV files are supported for voice notes.'}, status=400)
                try:
                    transcribed_text = convert_voice_to_text(voice_note)
                    if not transcribed_text:
                        return JsonResponse({'error': 'Could not convert voice note to text. Please try again.'}, status=400)
                    
                    # Return only the transcribed text for frontend review
                    return JsonResponse({'transcribed_text': transcribed_text})

                except Exception as e:
                    print(f"Error converting voice note: {str(e)}")
                    return JsonResponse({'error': 'Error processing voice note. Please try again.'}, status=500)
            else:
                 return JsonResponse({'error': 'No voice note file provided.'}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data.'}, status=400)
        except Exception as e:
            import traceback
            print("Error in diagnose view:", e)
            print(traceback.format_exc())
            return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Only POST requests are accepted.'}, status=405)

@csrf_exempt
def process_text_message(request):
    """API endpoint to process text messages and return medical advice"""
    if request.method == 'POST':
        try:
            # Handle both JSON and form data
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                user_symptoms = data.get('symptoms', '').strip()
                images = []  # No images in JSON request
            else:
                # Handle multipart form data
                user_symptoms = request.POST.get('symptoms', '').strip()
                images = request.FILES.getlist('images', [])
            
            if not user_symptoms and not images:
                return JsonResponse({'error': 'No symptoms or images provided.'}, status=400)

            try:
                # Search your custom medical knowledge
                context_texts = search_textbook(user_symptoms)

                # Process images if present
                image_data = []
                saved_images = []  # Store references to saved images
                
                for image in images:
                    try:
                        # Read image data in binary mode
                        image_bytes = image.read()
                        
                        # Validate image size (max 5MB)
                        if len(image_bytes) > 5 * 1024 * 1024:
                            print(f"Image too large: {len(image_bytes)} bytes")
                            continue
                            
                        # Validate mime type
                        if not image.content_type.startswith('image/'):
                            print(f"Invalid mime type: {image.content_type}")
                            continue
                            
                        # Convert GIF to JPEG if needed
                        if image.content_type == 'image/gif':
                            try:
                                from PIL import Image
                                import io
                                
                                # Open the GIF
                                img = Image.open(io.BytesIO(image_bytes))
                                
                                # Convert to RGB (removes alpha channel if present)
                                if img.mode in ('RGBA', 'LA'):
                                    background = Image.new('RGB', img.size, (255, 255, 255))
                                    background.paste(img, mask=img.split()[-1])
                                    img = background
                                elif img.mode != 'RGB':
                                    img = img.convert('RGB')
                                
                                # Save as JPEG
                                jpeg_buffer = io.BytesIO()
                                img.save(jpeg_buffer, format='JPEG', quality=85)
                                image_bytes = jpeg_buffer.getvalue()
                                image.content_type = 'image/jpeg'
                                
                                print(f"Converted GIF to JPEG: {len(image_bytes)} bytes")
                            except Exception as e:
                                print(f"Error converting GIF to JPEG: {str(e)}")
                                continue
                            
                        # Convert to base64 safely
                        import base64
                        image_b64 = base64.b64encode(image_bytes).decode('ascii')
                        
                        # Add to image data list
                        image_data.append({
                            'mime_type': image.content_type,
                            'data': image_b64
                        })
                        
                        # Save image to database
                        chat_image = ChatImage.objects.create(
                            user=request.user,
                            image=image
                        )
                        saved_images.append(chat_image)
                        
                        print(f"Successfully processed and saved image: {image.name}, type: {image.content_type}, size: {len(image_bytes)} bytes")
                    except Exception as e:
                        print(f"Error processing image: {str(e)}")
                        continue

                # Ask Gemini with both text and images
                answer = ask_gemini(user_symptoms, context_texts, request.user, image_data, saved_images)

                # Extract and save medication recommendations if present
                if "Recommended Medication" in answer:
                    try:
                        # Split the answer to get the medication section
                        med_section = answer.split("Recommended Medication")[1].split("\n\n")[0]
                        
                        # Extract medication details
                        lines = med_section.split("\n")
                        medication_name = lines[0].strip()
                        
                        # Extract dosage if present
                        dosage = ""
                        for line in lines:
                            if "Dosage:" in line:
                                dosage = line.split("Dosage:")[1].strip()
                                break
                        
                        # Create medication recommendation
                        MedicationRecommendation.objects.create(
                            user=request.user,
                            medication_name=medication_name,
                            dosage=dosage,
                            frequency="",  # You might want to add more sophisticated parsing
                            duration="",   # You might want to add more sophisticated parsing
                            warnings="",   # You might want to add more sophisticated parsing
                            contraindications="",  # You might want to add more sophisticated parsing
                            chat_history=GeminiChatHistory.objects.filter(user=request.user, role="ai").latest('timestamp')
                        )
                    except Exception as e:
                        print(f"Error saving medication recommendation: {str(e)}")

                # Return response with proper image URLs
                return JsonResponse({
                    'answer': answer,
                    'images': [{
                        'url': request.build_absolute_uri(img.image.url) if img.image else None,
                        'id': img.id
                    } for img in saved_images if img.image]
                })
            except requests.exceptions.Timeout:
                return JsonResponse({
                    'error': 'The request to the AI service timed out. Please check your internet connection and try again.',
                    'status': 'timeout'
                }, status=504)
            except requests.exceptions.ConnectionError:
                return JsonResponse({
                    'error': 'Unable to connect to the AI service. Please check your internet connection and try again.',
                    'status': 'connection_error'
                }, status=503)
            except Exception as e:
                print(f"Error in Gemini processing: {str(e)}")
                return JsonResponse({
                    'error': 'An error occurred while processing your request. Please try again.',
                    'status': 'error',
                    'details': str(e)
                }, status=500)
        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data.'}, status=400)
        except Exception as e:
            import traceback
            print("Error in process_text_message view:", e)
            print(traceback.format_exc())
            return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Only POST requests are accepted.'}, status=405)

def convert_voice_to_text(audio_file):
    """Convert uploaded audio file to text"""
    temp_files = []  # Keep track of all temporary files
    try:
        print(f"Processing audio file: {audio_file.name}, size: {audio_file.size} bytes")
        
        # Create temporary file for the original audio
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_files.append(temp_file.name)
        for chunk in audio_file.chunks():
            temp_file.write(chunk)
        temp_file.flush()
        temp_file.close()  # Close the file handle
        print(f"Saved temporary file: {temp_file.name}")

        try:
            # Convert to proper WAV if needed
            print("Loading audio file with pydub...")
            audio = AudioSegment.from_file(temp_file.name)
            print(f"Audio loaded successfully. Duration: {len(audio)/1000} seconds")
            
            # Split into 30-second chunks
            chunk_length_ms = 30 * 1000
            chunks = make_chunks(audio, chunk_length_ms)
            print(f"Split audio into {len(chunks)} chunks")

            recognizer = sr.Recognizer()
            full_text = ""

            for i, chunk in enumerate(chunks):
                print(f"Processing chunk {i+1}/{len(chunks)}")
                chunk_file = tempfile.NamedTemporaryFile(suffix=f"_chunk{i}.wav", delete=False)
                temp_files.append(chunk_file.name)
                chunk.export(chunk_file.name, format="wav")
                chunk_file.close()  # Close the file handle
                print(f"Exported chunk to: {chunk_file.name}")

                try:
                    with sr.AudioFile(chunk_file.name) as source:
                        print(f"Reading audio data from chunk {i+1}")
                        audio_data = recognizer.record(source)
                        print(f"Sending chunk {i+1} to Google Speech Recognition")
                        text = recognizer.recognize_google(audio_data)
                        print(f"Received text for chunk {i+1}: {text}")
                        full_text += text + " "
                except sr.UnknownValueError:
                    print(f"Chunk {i+1}: Could not understand audio")
                except sr.RequestError as e:
                    print(f"Chunk {i+1}: API request error - {e}")
                    raise
                except Exception as e:
                    print(f"Chunk {i+1}: Unexpected error - {e}")
                    raise

            if not full_text.strip():
                print("No text was recognized from the audio")
                return None
                
            print(f"Final recognized text: {full_text.strip()}")
            return full_text.strip()
            
        except Exception as e:
            print(f"Error processing audio file: {str(e)}")
            import traceback
            print(traceback.format_exc())
            raise
            
    except Exception as e:
        print(f"Error in convert_voice_to_text: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise
    finally:
        # Clean up all temporary files
        import time
        for file_path in temp_files:
            try:
                # Add a small delay to ensure files are released
                time.sleep(0.1)
                if os.path.exists(file_path):
                    os.unlink(file_path)
                    print(f"Cleaned up temporary file: {file_path}")
            except Exception as e:
                print(f"Warning: Could not delete temporary file {file_path}: {e}")

def get_hospitals_nearby_from_user_location(user):
    """
    Get nearby hospitals based on user's location data from their profile.
    Args:
        user: A User object that has a profile attribute
    Returns:
        list: A list of nearby hospitals with their details
    """
    try:
        # Get the user's profile
        profile = user.profile
        
        # Get location data
        city = profile.city
        state = profile.state
        country = profile.country
        lat = profile.lat
        lon = profile.lon

        # First try to search by city, state, country
        location = f"hospital in {city}, {state}, {country}"
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": location,
            "format": "json",
            "limit": 7,
        }
        headers = {
             "User-Agent": "MedicalChatbotLocal/0.1"
        }
        
        try:
            response = requests.get(url, params=params, headers=headers)
            results = response.json()

            # If no results and we have coordinates, try searching by coordinates
            if not results and lat and lon:
                params = {
                    "q": "hospital",
                    "format": "json",
                    "limit": 7,
                    "bounded": 1,
                    "viewbox": f"{lon - 0.05},{lat + 0.05},{lon + 0.05},{lat - 0.05}"
                }
                response = requests.get(url, params=params, headers=headers)
                results = response.json()

            # Format the results to include display name and address
            formatted_results = []
            for result in results:
                formatted_result = {
                    'display_name': result.get('display_name', 'Unknown Hospital'),
                    'address': result.get('display_name', '').split(',')[0],  # Get the first part of the address
                    'lat': result.get('lat'),
                    'lon': result.get('lon')
                }
                formatted_results.append(formatted_result)

            return formatted_results
        except Exception as e:
            print(f"Error fetching hospitals: {str(e)}")
            return []
    except Exception as e:
        print(f"Error accessing user profile: {str(e)}")
        return []



@login_required(login_url='login')
def settings(request):
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)

    if request.method == 'POST':
        # Get all submitted form data from POST
        profile.gender = request.POST.get('gender', '')
        profile.ethnicity = request.POST.get('ethnicity', '')
        profile.smoking_status = request.POST.get('smoking_status', '')
        profile.alcohol_use = request.POST.get('alcohol_use', '')
        profile.physical_activity = request.POST.get('physical_activity', '')
        
        profile.known_allergies = request.POST.get('known_allergies', '')
        profile.current_medications = request.POST.get('current_medications', '')
        profile.chronic_conditions = request.POST.get('chronic_conditions', '')
        profile.family_history = request.POST.get('family_history', '')

        profile.is_pregnant = request.POST.get('is_pregnant') == 'on'

        # Convert to int safely with defaults
        try:
            profile.age = int(request.POST.get('age', 0))
        except ValueError:
            profile.age = 0
        try:
            profile.weight = int(request.POST.get('weight', 0))
        except ValueError:
            profile.weight = 0
        try:
            profile.height = int(request.POST.get('height', 0))
        except ValueError:
            profile.height = 0

        profile.city = request.POST.get('city', '')
        profile.state = request.POST.get('state', '')
        profile.country = request.POST.get('country', '')

        try:
            profile.lat = float(request.POST.get('lat', 0))
        except ValueError:
            profile.lat = 0
        try:
            profile.lon = float(request.POST.get('lon', 0))
        except ValueError:
            profile.lon = 0

        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']

        profile.save()
        return redirect('settings')   
    user.refresh_from_db()
    profile = user.profile
    
    context = {
        'user': user,
        'GENDER_CHOICES': [
            ('male', 'Male'),
            ('female', 'Female'),
        ],
        'ETHNICITY_CHOICES': [
            ('african', 'African'),
            ('african_american', 'African American'),
            ('white', 'White / Caucasian'),
            ('hispanic', 'Hispanic / Latino'),
            ('asian', 'Asian'),
            ('south_asian', 'South Asian (e.g., Indian, Pakistani)'),
            ('native_american', 'Native American / Alaska Native'),
            ('pacific_islander', 'Native Hawaiian / Pacific Islander'),
            ('middle_eastern', 'Middle Eastern / North African'),
            ('mixed', 'Mixed / Multiracial'),
            ('other', 'Other'),
        ],
        'SMOKING_STATUS': [
            ('never', 'Never'),
            ('former', 'Former'),
            ('current', 'Current Smoker'),
        ],
        'ALCOHOL_USAGE': [
            ('none', 'None'),
            ('occasional', 'Occasional'),
            ('frequent', 'Frequent'),
        ],
        'ACTIVITY_LEVEL': [
            ('sedentary', 'Sedentary'),
            ('moderate', 'Moderate'),
            ('active', 'Active'),
        ],
    }
    return render(request, 'settings.html', context)

@login_required
@require_http_methods(["POST"])
def generate_report(request):
    try:
        data = json.loads(request.body)
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')
        report_type = data['report_type']

        # Get all chats within the date range
        chats = GeminiChatHistory.objects.filter(
            user=request.user,
            timestamp__range=[start_date, end_date]
        ).order_by('timestamp')

        # Prepare chat history for Gemini
        chat_history = []
        for chat in chats:
            chat_history.append({
                'role': chat.role,
                'message': chat.message,
                'timestamp': chat.timestamp.strftime('%Y-%m-%d %H:%M')
            })

        # Create prompt for Gemini based on report type
        if report_type == 'summary':
            prompt = f"""Based on the following medical consultation history, generate a comprehensive medical summary report. 
            Format the response in plain text with clear sections. Include:
            1. Overview of Consultations
            2. Key Symptoms Identified
            3. Main Concerns Discussed
            4. Recommendations Provided
            5. Follow-Up Suggestions
            
            Chat History:
            {json.dumps(chat_history, indent=2)}
            
            Please provide a clear, well-structured report."""
            
        elif report_type == 'detailed':
            prompt = f"""Generate a detailed medical report from the following consultation history. 
            Format the response in plain text with clear sections. Include:
            1. Chronological Timeline
            2. Symptom Analysis
            3. Medical Advice
            4. Treatment Recommendations
            5. Lifestyle Suggestions
            
            Chat History:
            {json.dumps(chat_history, indent=2)}
            
            Please provide a clear, well-structured report."""
            
        elif report_type == 'symptoms':
            prompt = f"""Analyze the following medical consultation history and create a symptoms-focused report. 
            Format the response in plain text with clear sections. Include:
            1. Symptom Timeline
            2. Severity Progression
            3. Related Symptoms
            4. Trigger Factors
            5. Management Recommendations
            
            Chat History:
            {json.dumps(chat_history, indent=2)}
            
            Please provide a clear, well-structured report."""
        else:
            return JsonResponse({'error': 'Invalid report type'}, status=400)

        # Get response from Gemini
        try:
            report_text = ask_gemini(prompt, [], request.user)
            
            # Clean the text
            report_text = report_text.replace('\x00', '')
            
            # Clean up emojis and markdown
            def clean_text(text):
                # Remove emojis
                emoji_pattern = re.compile("["
                    u"\U0001F600-\U0001F64F"  # emoticons
                    u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                    u"\U0001F680-\U0001F6FF"  # transport & map symbols
                    u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                    u"\U00002702-\U000027B0"
                    u"\U000024C2-\U0001F251"
                    "]+", flags=re.UNICODE)
                text = emoji_pattern.sub('', text)
                
                # Remove HTML tags
                text = re.sub(r'<[^>]+>', '', text)
                
                # Convert markdown to plain text
                text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Remove bold
                text = re.sub(r'\*(.*?)\*', r'\1', text)      # Remove italic
                text = re.sub(r'\[(.*?)\]', r'\1', text)      # Remove links
                text = re.sub(r'#+ (.*)', r'\1', text)        # Remove headers
                text = re.sub(r'`(.*?)`', r'\1', text)        # Remove code blocks
                
                # Format numbered sections
                text = re.sub(r'(\d+\.\s*[A-Za-z\s]+:)', r'\n\1\n', text)  # Add newlines around numbered sections
                
                # Format bullet points
                text = re.sub(r'[•*]\s*', '\n• ', text)  # Add newline before bullet points
                text = re.sub(r'•\s*•\s*', '    • ', text)  # Format nested bullet points
                
                # Add spacing after sections
                text = re.sub(r'([A-Za-z\s]+:)\n', r'\1\n\n', text)  # Add extra newline after section headers
                
                # Remove duplicate sections
                text = re.sub(r'(Nearby Hospitals:.*?)(?=Nearby Hospitals:)', r'\1', text, flags=re.DOTALL)
                
                # Clean up whitespace
                text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Replace multiple newlines with double newline
                text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
                text = text.strip()
                
                # Split into sections and format each section
                sections = text.split('\n\n')
                formatted_sections = []
                
                for section in sections:
                    if section.strip():
                        # Format section headers
                        if section.strip().endswith(':'):
                            formatted_sections.append(f"\n{section.strip()}\n")
                        else:
                            # Format bullet points
                            lines = section.split('\n')
                            formatted_lines = []
                            for line in lines:
                                if line.strip():
                                    if line.strip().startswith('•'):
                                        # Handle nested bullet points
                                        if '    •' in line:
                                            formatted_lines.append(f"    {line.strip()}")
                                        else:
                                            formatted_lines.append(line.strip())
                                    else:
                                        formatted_lines.append(line.strip())
                            formatted_sections.append('\n'.join(formatted_lines))
                
                # Join sections with proper spacing
                formatted_text = '\n\n'.join(formatted_sections)
                
                # Add extra spacing after main sections
                formatted_text = re.sub(r'(\d+\.\s*[A-Za-z\s]+:.*?)(?=\d+\.\s*[A-Za-z\s]+:|$)', 
                                       r'\1\n\n', formatted_text, flags=re.DOTALL)
                
                return formatted_text
            
            # Clean the report text
            report_text = clean_text(report_text)
            
            # Return JSON response with download URL
            return JsonResponse({
                'report_html': report_text,
                'download_url': f'/download_report/?start_date={start_date.strftime("%Y-%m-%d")}&end_date={end_date.strftime("%Y-%m-%d")}&report_type={report_type}'
            })
            
        except Exception as e:
            print(f"Error generating report: {str(e)}")
            return JsonResponse({'error': f'Failed to generate report: {str(e)}'}, status=500)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def download_report(request):
    try:
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        report_type = request.GET.get('report_type')

        if not all([start_date, end_date, report_type]):
            return JsonResponse({'error': 'Missing required parameters'}, status=400)

        # Convert string dates to datetime objects
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

        # Get all chats within the date range
        chats = GeminiChatHistory.objects.filter(
            user=request.user,
            timestamp__range=[start_date, end_date]
        ).order_by('timestamp')

        # Prepare chat history for Gemini
        chat_history = []
        for chat in chats:
            chat_history.append({
                'role': chat.role,
                'message': chat.message,
                'timestamp': chat.timestamp.strftime('%Y-%m-%d %H:%M')
            })

        # Create prompt for Gemini based on report type
        if report_type == 'summary':
            prompt = f"""Based on the following medical consultation history, generate a comprehensive medical summary report. 
            Format the response in plain text with clear sections. Include:
            1. Overview of Consultations
            2. Key Symptoms Identified
            3. Main Concerns Discussed
            4. Recommendations Provided
            5. Follow-Up Suggestions
            
            Chat History:
            {json.dumps(chat_history, indent=2)}
            
            Please provide a clear, well-structured report."""
            
        elif report_type == 'detailed':
            prompt = f"""Generate a detailed medical report from the following consultation history. 
            Format the response in plain text with clear sections. Include:
            1. Chronological Timeline
            2. Symptom Analysis
            3. Medical Advice
            4. Treatment Recommendations
            5. Lifestyle Suggestions
            
            Chat History:
            {json.dumps(chat_history, indent=2)}
            
            Please provide a clear, well-structured report."""
            
        elif report_type == 'symptoms':
            prompt = f"""Analyze the following medical consultation history and create a symptoms-focused report. 
            Format the response in plain text with clear sections. Include:
            1. Symptom Timeline
            2. Severity Progression
            3. Related Symptoms
            4. Trigger Factors
            5. Management Recommendations
            
            Chat History:
            {json.dumps(chat_history, indent=2)}
            
            Please provide a clear, well-structured report."""
        else:
            return JsonResponse({'error': 'Invalid report type'}, status=400)

        # Get response from Gemini
        try:
            report_text = ask_gemini(prompt, [], request.user)
            
            # Clean the text and remove null bytes
            report_text = report_text.replace('\x00', '')
            
            # Create HTML content with CSS styling
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    @page {{
                        margin: 2.5cm;
                        size: letter;
                    }}
                    body {{
                        font-family: Helvetica, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        padding: 20px;
                    }}
                    .title {{
                        text-align: center;
                        font-size: 24pt;
                        color: #2c3e50;
                        margin-bottom: 30px;
                        font-weight: bold;
                    }}
                    .section {{
                        margin-bottom: 30px;
                    }}
                    .section-header {{
                        font-size: 16pt;
                        color: #3498db;
                        border-bottom: 2px solid #3498db;
                        padding-bottom: 5px;
                        margin-bottom: 15px;
                        font-weight: bold;
                    }}
                    .bullet-list {{
                        margin-left: 20px;
                        margin-bottom: 15px;
                    }}
                    .bullet-item {{
                        margin-bottom: 12px;
                        position: relative;
                        padding-left: 20px;
                    }}
                    .bullet-item:before {{
                        content: "•";
                        position: absolute;
                        left: 0;
                        color: #3498db;
                    }}
                    .nested-bullet {{
                        margin-left: 40px;
                        margin-top: 8px;
                        margin-bottom: 8px;
                    }}
                    .disclaimer {{
                        text-align: center;
                        font-style: italic;
                        color: #666;
                        margin-top: 40px;
                        padding: 20px;
                        border-top: 1px solid #ddd;
                    }}
                </style>
            </head>
            <body>
                <div class="title">Medical Report ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})</div>
            """

            # Split the report text into sections and format as HTML
            sections = report_text.split('\n\n')
            for section in sections:
                if section.strip():
                    if section.strip().endswith(':'):
                        # This is a section header
                        html_content += f'<div class="section"><div class="section-header">{section.strip()}</div>'
                    else:
                        # This is content with bullet points
                        lines = section.split('\n')
                        html_content += '<div class="bullet-list">'
                        for line in lines:
                            if line.strip():
                                if line.strip().startswith('•'):
                                    if '    •' in line:
                                        # Nested bullet point
                                        html_content += f'<div class="bullet-item nested-bullet">{line.strip().replace("    •", "").strip()}</div>'
                                    else:
                                        # Regular bullet point
                                        html_content += f'<div class="bullet-item">{line.strip().replace("•", "").strip()}</div>'
                                else:
                                    # Regular text
                                    html_content += f'<div class="bullet-item">{line.strip()}</div>'
                        html_content += '</div>'
                    html_content += '</div>'

            # Add disclaimer
            html_content += """
                <div class="disclaimer">
                    Remember: This report is based on the information provided and does not substitute professional medical advice!
                </div>
            </body>
            </html>
            """

            try:
                # Create PDF using xhtml2pdf
                pdf = BytesIO()
                pisa_status = pisa.CreatePDF(
                    html_content,
                    dest=pdf,
                    encoding='utf-8'
                )
                
                if pisa_status.err:
                    return JsonResponse({'error': 'Failed to generate PDF'}, status=500)
                
                # Get the value of the BytesIO buffer
                pdf.seek(0)
                pdf_data = pdf.getvalue()
                pdf.close()
                
                # Create the HTTP response
                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="medical_report_{start_date.strftime("%Y-%m-%d")}_to_{end_date.strftime("%Y-%m-%d")}.pdf"'
                response.write(pdf_data)
                
                return response
            except Exception as e:
                print(f"Error generating PDF: {str(e)}")
                return JsonResponse({'error': f'Failed to generate PDF: {str(e)}'}, status=500)

        except Exception as e:
            print(f"Error in download_report: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    except Exception as e:
        print(f"Error in download_report: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

def clean_text(text):
    # Remove emojis
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    text = emoji_pattern.sub('', text)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Convert markdown to plain text
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Remove bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # Remove italic
    text = re.sub(r'\[(.*?)\]', r'\1', text)      # Remove links
    text = re.sub(r'#+ (.*)', r'\1', text)        # Remove headers
    text = re.sub(r'`(.*?)`', r'\1', text)        # Remove code blocks
    
    # Format numbered sections
    text = re.sub(r'(\d+\.\s*[A-Za-z\s]+:)', r'\n\1\n', text)  # Add newlines around numbered sections
    
    # Format bullet points
    text = re.sub(r'[•*]\s*', '\n• ', text)  # Add newline before bullet points
    text = re.sub(r'•\s*•\s*', '    • ', text)  # Format nested bullet points
    
    # Add spacing after sections
    text = re.sub(r'([A-Za-z\s]+:)\n', r'\1\n\n', text)  # Add extra newline after section headers
    
    # Remove duplicate sections
    text = re.sub(r'(Nearby Hospitals:.*?)(?=Nearby Hospitals:)', r'\1', text, flags=re.DOTALL)
    
    # Clean up whitespace
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Replace multiple newlines with double newline
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
    text = text.strip()
    
    # Split into sections and format each section
    sections = text.split('\n\n')
    formatted_sections = []
    
    for section in sections:
        if section.strip():
            # Format section headers
            if section.strip().endswith(':'):
                formatted_sections.append(f"\n{section.strip()}\n")
            else:
                # Format bullet points
                lines = section.split('\n')
                formatted_lines = []
                for line in lines:
                    if line.strip():
                        if line.strip().startswith('•'):
                            # Handle nested bullet points
                            if '    •' in line:
                                formatted_lines.append(f"    {line.strip()}")
                            else:
                                formatted_lines.append(line.strip())
                        else:
                            formatted_lines.append(line.strip())
                formatted_sections.append('\n'.join(formatted_lines))
    
    # Join sections with proper spacing
    formatted_text = '\n\n'.join(formatted_sections)
    
    # Add extra spacing after main sections
    formatted_text = re.sub(r'(\d+\.\s*[A-Za-z\s]+:.*?)(?=\d+\.\s*[A-Za-z\s]+:|$)', 
                           r'\1\n\n', formatted_text, flags=re.DOTALL)
    
    return formatted_text

 
