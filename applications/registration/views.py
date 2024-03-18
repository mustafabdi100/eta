import random
import string
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required,permission_required
from .forms import BusinessDetailForm, CustomUserCreationForm,ContactPersonForm,CreditCardForm
from .models import BusinessDetail, CreditCard,ContactPerson,ActivityLog
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.files import File
from .utils import ensure_tmp_directory_exists
from django.conf import settings
import os
from django.db.models import Q
from .decorators import form_step_required
from django.core.paginator import Paginator

import json
from django.http import JsonResponse

def get_cities(request, country):
    with open('data.json', encoding='utf-8') as file:
        data = json.load(file)
        selected_country = next(c for c in data if c['country'] == country)
        cities = selected_country['city']
        return JsonResponse(cities, safe=False)

def home(request):
    return render(request, 'registration/home.html')


def business_detail_view(request):
    initial_data = request.session.get('business_details', {})
    if request.method == 'POST':
        form = BusinessDetailForm(request.POST, request.FILES)
        if form.is_valid():
            ensure_tmp_directory_exists()
            business_data = form.cleaned_data.copy()

            # Concatenate phone code and phone number
            phone_code = business_data.get('phone_code')
            phone_number = business_data.get('phone_number')
            if phone_code and phone_number:
                business_data['phone_number'] = f"{phone_code}{phone_number}"

            for file_field in ['registration_certificate', 'trading_license', 'tax_compliance_certificate']:
                if file_field in request.FILES:
                    file = request.FILES[file_field]
                    unique_filename = f"{file_field}_{request.session.session_key}_{file.name}"
                    path = default_storage.save('tmp/' + unique_filename, ContentFile(file.read()))
                    business_data[file_field] = path

            request.session['business_details'] = business_data
            return redirect('contact_person_view')
    else:
        form = BusinessDetailForm(initial=initial_data)

    return render(request, 'registration/business_detail.html', {'form': form})

@form_step_required('business_details', 'business_detail_view')

def contact_person_view(request):
    # Get the existing contact person data from the session
    existing_contact_person = request.session.get('contact_person', {})

    if request.method == 'POST':
        form = ContactPersonForm(request.POST)
        if form.is_valid():
            contact_person_data = form.cleaned_data
            request.session['contact_person'] = contact_person_data
            request.session.modified = True  # Ensure the session is saved
            return redirect('credit_card_view')
    else:
        # If GET request or form is invalid, initialize the form with existing data
        form = ContactPersonForm(initial=existing_contact_person)

    context = {
        'form': form,
    }
    return render(request, 'registration/contact_person.html', context)

@form_step_required('contact_person', 'contact_person_view')
def credit_card_view(request):
    # Get the existing credit card data from the session
    existing_credit_card = request.session.get('credit_card', {})

    if request.method == 'POST':
        form = CreditCardForm(request.POST)
        if form.is_valid():
            credit_card_data = form.cleaned_data
            request.session['credit_card'] = credit_card_data
            request.session.modified = True  # Ensure the session is saved
            return redirect('review_application')
    else:
        # If GET request or form is invalid, initialize the form with existing data
        form = CreditCardForm(initial=existing_credit_card)

    context = {
        'form': form,
    }
    return render(request, 'registration/credit_card.html', context)



def review_application(request):
    # Fetch data from session
    business_details = request.session.get('business_details', {})
    contact_person = request.session.get('contact_person', {})
    credit_card = request.session.get('credit_card', {})

    # Context to display the data for review
    context = {
        'business_details': business_details,
        'contact_person': contact_person,
        'credit_card': credit_card,
    }

    return render(request, 'registration/review_application.html', context)

def generate_unique_reference():
    while True:
        reference = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        if not BusinessDetail.objects.filter(reference_number=reference).exists():
            return reference

def final_submission_view(request):
    if request.method == 'POST':
        # Ensure there's data to submit
        if 'business_details' in request.session and 'contact_person' in request.session and 'credit_card' in request.session:
            # Retrieve data from session
            business_details_data = request.session.pop('business_details')
            contact_person_data = request.session.pop('contact_person')
            credit_card_data = request.session.pop('credit_card')

            # Generate a unique reference number
            reference_number = generate_unique_reference()
            business_details_data['reference_number'] = reference_number

            # Exclude file fields from initial creation to avoid issues with unsaved model instance
            file_fields = ['registration_certificate', 'trading_license', 'tax_compliance_certificate']
            file_data = {field: business_details_data.pop(field) for field in file_fields if field in business_details_data}

            # Create the BusinessDetail instance without file fields
            business_detail = BusinessDetail.objects.create(**business_details_data)

            # Handle file uploads
            for file_field, temp_file_path in file_data.items():
                if temp_file_path:
                    # Use Django's default storage API to open the file. This works with S3 if configured.
                    with default_storage.open(temp_file_path, 'rb') as file:
                        # Save the file to the model
                        getattr(business_detail, file_field).save(os.path.basename(temp_file_path), File(file), save=True)

            # Create ContactPerson instance
            ContactPerson.objects.create(business=business_detail, **contact_person_data)

            # Create CreditCard instance
            CreditCard.objects.create(business=business_detail, **credit_card_data)

            # Clear session data for contact person and credit card to prevent re-use
            if 'contact_person' in request.session:
                del request.session['contact_person']
            if 'credit_card' in request.session:
                del request.session['credit_card']

            # Return the reference number as a JSON response
            return JsonResponse({'reference_number': reference_number})

    # If there's no data in the session (e.g., direct access), redirect to the start of the form process
    return redirect('business_detail_view')



@login_required
def dashboard_view(request):
    total_applications = BusinessDetail.objects.count()
    pending_applications = BusinessDetail.objects.filter(status='pending').count()
    approved_applications = BusinessDetail.objects.filter(status='approved').count()
    rejected_applications = BusinessDetail.objects.filter(status='rejected').count()
    all_applications = BusinessDetail.objects.all()

    # Pagination
    paginator = Paginator(all_applications, 10)  # Show 10 applications per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'approved_applications': approved_applications,
        'rejected_applications': rejected_applications,
        'page_obj': page_obj,  # Pass the paginated data
    }
    return render(request, 'registration/dashboard.html', context)

@login_required
def pending_applications_view(request):
    pending_applications = BusinessDetail.objects.filter(status='pending')

    # Pagination
    paginator = Paginator(pending_applications, 10)  # Show 10 applications per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,  # Pass the paginated data
    }
    return render(request, 'registration/pending_applications.html', context)

@login_required
def approved_applications_view(request):
    approved_applications = BusinessDetail.objects.filter(status='approved')
    
    # Pagination
    paginator = Paginator(approved_applications, 10)  # Show 10 applications per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,  # Pass the paginated data
    }
    return render(request, 'registration/approved_applications.html', context)

@login_required
def rejected_applications_view(request):
    rejected_applications = BusinessDetail.objects.filter(status='rejected')

    # Pagination
    paginator = Paginator(rejected_applications, 10)  # Show 10 applications per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,  # Pass the paginated data
    }
    return render(request, 'registration/rejected_applications.html', context)

@login_required
def application_review_view(request, application_id):
    application = get_object_or_404(BusinessDetail, id=application_id)
    is_rejected = application.status == 'rejected'
    
    if request.method == "POST":
        if 'approve' in request.POST and not is_rejected:
            application.status = 'approved'
            application.save()
            ActivityLog.objects.create(user=request.user, action='approval', description=f'Application with reference number {application.reference_number} approved.')
            return redirect('dashboard_view')
        elif 'reject' in request.POST and not is_rejected:
            application.status = 'rejected'
            application.save()
            ActivityLog.objects.create(user=request.user, action='rejection', description=f'Application with reference number {application.reference_number} rejected.')
            return redirect('dashboard_view')
    
    context = {
        'application': application,
        'is_rejected': is_rejected,
    }
    return render(request, 'registration/application_review.html', context)


@login_required
def reject_application(request, application_id):
    application = get_object_or_404(BusinessDetail, id=application_id)
    application.status = 'rejected'
    application.save()
    ActivityLog.objects.create(user=request.user, action='rejection', description=f'Application {application_id} rejected.')
    return redirect('approved_applications_view')



@login_required
@permission_required('yourapp.view_activitylog', raise_exception=True)
def view_activity_logs(request):
    logs = ActivityLog.objects.all().order_by('-timestamp')
    return render(request, 'registration/view_activity_logs.html', {'logs': logs})

def search_application_status(request):
    if request.method == 'POST':
        business_name = request.POST.get('business_name', '').strip()
        reference_number = request.POST.get('reference_number', '').strip()

        # Check if either business_name or reference_number is provided
        if business_name or reference_number:
            query = Q()

            # If reference_number is provided, search by reference_number (case-insensitive)
            if reference_number:
                query |= Q(reference_number__iexact=reference_number)

            # If business_name is provided, search by business_name (case-insensitive exact match)
            if business_name:
                query |= Q(business_name__iexact=business_name)

            applications = BusinessDetail.objects.filter(query)
            if applications:
                application_data = []
                for application in applications:
                    application_data.append({
                        'status': application.status,
                    })
                return JsonResponse({'applications': application_data})
            else:
                return JsonResponse({'error_message': 'No application found with the provided details.'})

    return JsonResponse({'error_message': 'Invalid request method.'})
