from datetime import datetime, timedelta
from django import forms


class AvailabilityForm(forms.Form):
    """Creates the availability form on the UI."""
    email = forms.EmailField()

    date_choices = [(str(datetime.now().date() + timedelta(days=i)),
                    (datetime.now() + timedelta(days=i)).strftime('%A, %B %d, %Y'))
                    for i in range(14)]
    date = forms.ChoiceField(choices=date_choices, widget=forms.Select(
        attrs={'class': 'form-control'}))

    hour_choices = [(f'{hour:02}:00', f'{hour:02}:00')
                    for hour in range(6, 22)]

    time = forms.ChoiceField(choices=hour_choices, widget=forms.Select(
        attrs={'class': 'form-control'}))
