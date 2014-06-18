# -*- coding: utf-8 -*

from django.shortcuts import render
from django import forms
from lots_admin.models import Lot, Application, Address
import requests

CARTODB = 'http://datamade.cartodb.com/api/v2/sql'

class ApplicationForm(forms.Form):
    lot_1_address = forms.CharField(
        error_messages={'required': 'Provide the lot’s address'})
    lot_1_pin = forms.CharField(
        error_messages={
            'required': 'Provide the lot’s Parcel Identification Number'
        })
    lot_1_use = forms.ChoiceField(choices=Lot.USE_CHOICES,required=False)
    lot_2_address = forms.CharField(required=False)
    lot_2_pin = forms.CharField(required=False)
    lot_2_use = forms.ChoiceField(choices=Lot.USE_CHOICES,required=False)
    owned_address = forms.CharField(
        error_messages={
            'required': 'Provide the address of the building you own'
        })
    deed_image = forms.FileField(
        error_messages={'required': 'Provide an image of the deed of the building you own'
        })
    first_name = forms.CharField(error_messages={'required': 'Provide your first name'})
    last_name = forms.CharField(error_messages={'required': 'Provide your last name'})
    organization = forms.CharField(required=False)
    phone = forms.CharField(error_messages={'required': 'Provide a contact phone number'})
    email = forms.CharField(required=False)
    contact_street = forms.CharField(error_messages={'required': 'Provide a complete address'})
    contact_city = forms.CharField()
    contact_state = forms.CharField()
    contact_zip_code = forms.CharField()
    how_heard = forms.CharField(required=False)

def home(request):
    return render(request, 'index.html')

def get_lot_address(pin=None, address=None):
    if pin:
        query = 'select * from egp_parcels where pin14 = cast(%s as text) limit 1'
        l1_add = requests.get(CARTODB, params={'q': query % pin})
        if l1_add.json().get('rows'):
            row = l1_add.json()['rows'][0]
            l1_address = '%s %s %s %s' % (
                    row.get('street_number', ''),
                    row.get('street_dir', ''),
                    row.get('street_name', ''),
                    row.get('street_type', ''),
                )
            l1_add_info = {
                'street': l1_address,
                'city': 'Chicago',
                'state': 'IL',
            }
            l1_address, created = Address.objects.get_or_create(**l1_add_info)
    else:
        l1_address, created = Address.objects.get_or_create(street=address)
    return l1_address

def apply(request):
    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            l1_address = get_lot_address(pin=form.cleaned_data['lot_1_pin'], 
                address=form.cleaned_data['lot_1_address'])
            lot1_info = {
                'pin': form.cleaned_data['lot_1_pin'],
                'address': l1_address,
                'planned_use': form.cleaned_data.get('lot_1_use')
            }
            lot1, created = Lot.objects.get_or_create(**lot1_info)
            lot2 = None
            if form.cleaned_data.get('lot_2_pin'):
                l2_address = get_lot_address(pin=form.cleaned_data['lot_2_pin'], 
                    address=form.cleaned_data['lot_2_address'])
                lot2_info = {
                    'pin': form.cleaned_data['lot_2_pin'],
                    'address': l2_address,
                    'planned_use': form.cleaned_data.get('lot_2_use')
                }
                lot2, created = Lot.objects.get_or_create(**lot2_info)
            c_address_info = {
                'street': form.cleaned_data['contact_street'],
                'city': form.cleaned_data['contact_city'],
                'state': form.cleaned_data['contact_state'],
                'zip_code': form.cleaned_data['contact_zip_code']
            }
            c_address, created = Address.objects.get_or_create(**c_address_info)
            owned_address = get_lot_address(address=form.cleaned_data['owned_address'])
            app_info = {
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'organization': form.cleaned_data.get('organization'),
                'owned_address': owned_address,
                'deed_image': form.cleaned_data['deed_image'],
                'contact_address': c_address,
                'phone': form.cleaned_data['phone'],
                'email': form.cleaned_data.get('email'),
                'how_heard': form.cleaned_data.get('how_heard')
            }
            app = Application(**app_info)
            app.save()
            app.lot_set.add(lot1)
            if lot2:
                app.lot_set.add(lot2)
            app.save()
    else:
        form = ApplicationForm()
    return render(request, 'apply.html', {'form': form})

def status(request):
    return render(request, 'status.html')

def faq(request):
    return render(request, 'faq.html')

def about(request):
    return render(request, 'about.html')
