import requests
import datetime
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import UserPreference
from .forms import UserPreferenceForm,RegistrationForm


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful.')
            return redirect('login')
        else:
            messages.error(request, 'Unsuccessful registration. Invalid information.')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

@login_required
def update_preferences(request):
    user = request.user
    try:
        preferences = UserPreference.objects.get(user=user)
    except UserPreference.DoesNotExist:
        preferences = UserPreference(user=user)

    if request.method == 'POST':
        form = UserPreferenceForm(request.POST, instance=preferences)
        if form.is_valid():
            form.save()
            messages.success(request, 'Preferences updated successfully.')
            return redirect('home')
    else:
        form = UserPreferenceForm(instance=preferences)

    return render(request, 'update_preferences.html', {'form': form})

def get_weather_data(city, preferred_unit='metric'):
    api_key = '3b4e8cf2834f904744d2275bb2899ac9'
    weather_url = 'https://api.openweathermap.org/data/2.5/weather'
    forecast_url = 'https://api.openweathermap.org/data/2.5/forecast'
    
    params = {'q': city, 'appid': api_key, 'units': preferred_unit}
    
    # Current weather data
    response = requests.get(weather_url, params=params)
    response.raise_for_status()
    weather_data = response.json()
    
    if weather_data.get('cod') != 200:
        raise ValueError(weather_data.get('message', 'City not found'))
    
    # Forecast data
    response = requests.get(forecast_url, params=params)
    response.raise_for_status()
    forecast_data = response.json()
    
    return {
        'weather': weather_data,
        'forecast': forecast_data
    }

def get_city_image(city):
    api_key = 'AIzaSyC2UJgovcqX0NjQYS1UX7bDi-cR-hiQ4Vk'
    search_engine_id = '757bef36e6df3481a'
    query = f'{city} 1920x1080'
    url = f"https://www.googleapis.com/customsearch/v1"
    params = {
        'key': api_key,
        'cx': search_engine_id,
        'q': query,
        'searchType': 'image',
        'imgSize': 'xlarge'
    }
    
    default_image_url = './Static/default.jpg'  
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        search_items = data.get("items", [])
        if len(search_items) > 0:
            return search_items[0]['link']
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    
    return default_image_url

@login_required
def home(request):
    # Default values
    default_city = 'Rabat'
    default_unit = 'metric'
    unit_symbol = 'C'  # Default symbol for Celsius

    # Get user preferences if they exist
    user = request.user
    try:
        user_preference = UserPreference.objects.get(user=user)
        preferred_city = user_preference.favorite_location or default_city
        preferred_unit = 'imperial' if user_preference.preferred_unit == 'F' else 'metric'
        unit_symbol = 'F' if preferred_unit == 'imperial' else 'C'
    except UserPreference.DoesNotExist:
        preferred_city = default_city
        preferred_unit = default_unit

    # Get city from POST or use preferred city
    city = request.POST.get('city', preferred_city)

    context = {
        'day': datetime.date.today(),
        'city': city,
        'unit_symbol': unit_symbol,
        'exception_occurred': False
    }

    try:
        data = get_weather_data(city, preferred_unit)
        weather_data = data['weather']
        forecast_data = data['forecast']
        
        description = weather_data['weather'][0]['description']
        icon = weather_data['weather'][0]['icon']
        temp = weather_data['main']['temp']
        image_url = get_city_image(city)
        
        if not image_url:
            image_url = get_city_image(default_city)  # Fallback image
        
        # Process forecast data
        forecast_list = []
        for forecast in forecast_data['list']:
            date = forecast['dt_txt'].split(' ')[0]
            temp = forecast['main']['temp']
            description = forecast['weather'][0]['description']
            icon = forecast['weather'][0]['icon']
        
            # Check if there's already a forecast with the same date
            if any(item['date'] == date for item in forecast_list):
                continue  # Skip this forecast if the date already exists
        
            # Append the forecast to the list
            forecast_list.append({
                'date': date,
                'temp': temp,
                'description': description,
                'icon': icon
            })
    
            # Stop if we have 5 forecasts
            if len(forecast_list) == 5:
                break

        context.update({
            'description': description,
            'icon': icon,
            'temp': temp,
            'image_url': image_url,
            'forecast_list': forecast_list
        })

    except requests.RequestException:
        messages.error(request, 'Network error, please try again later.')
        context['exception_occurred'] = True

    except ValueError as e:
        messages.error(request, str(e))
        context['exception_occurred'] = True

    except KeyError:
        messages.error(request, 'Error processing weather data.')
        context['exception_occurred'] = True

    if context['exception_occurred']:
        data = get_weather_data(default_city, default_unit)
        weather_data = data['weather']
        forecast_data = data['forecast']
        
        forecast_list = []
        for forecast in forecast_data['list']:
            date = forecast['dt_txt'].split(' ')[0]
            temp = forecast['main']['temp']
            description = forecast['weather'][0]['description']
            icon = forecast['weather'][0]['icon']
            forecast_list.append({
                'date': date,
                'temp': temp,
                'description': description,
                'icon': icon
            })

        context.update({
            'description': weather_data['weather'][0]['description'],
            'icon': weather_data['weather'][0]['icon'],
            'temp': weather_data['main']['temp'],
            'city': default_city,
            'image_url': get_city_image(default_city),
            'forecast_list': forecast_list
        })
    return render(request, 'weatherapp/index.html', context)
