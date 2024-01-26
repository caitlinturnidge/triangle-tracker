# example/views.py
from datetime import datetime

from django.shortcuts import render
from dotenv import load_dotenv

from .forms import AvailabilityForm
from .resources import get_all_availabilities, verify_email, add_request

load_dotenv()


def index(request):
    form = AvailabilityForm()
    available_list = get_all_availabilities()

    if request.method == 'POST':

        form = AvailabilityForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            time = form.cleaned_data['time']
            date = form.cleaned_data['date']

            time_object = datetime.strptime(time, '%H:%M').time()
            date_object = datetime.strptime(date, '%Y-%m-%d').date()

            date_time = datetime.combine(date_object, time_object)

            verify_email(email)
            add_request(email, date_time)
            form = AvailabilityForm()
        else:
            form = AvailabilityForm()
            return render(request, 'availabilities.html', {'form': form, 'availabilities': available_list})

    return render(request, 'index.html', {'form': form})
