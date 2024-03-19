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
    existing_contact_persons = request.session.get('contact_person', [])

    if request.method == 'POST':
        forms = [ContactPersonForm(request.POST, prefix=str(i)) for i in range(1, 4)]
        if all(form.is_valid() for form in forms):
            contact_person_data = []
            for form in forms:
                if form.has_changed():
                    contact_person = form.save(commit=False)
                    contact_person.business = BusinessDetail.objects.last()
                    contact_person_dict = contact_person.__dict__.copy()
                    contact_person_dict.pop('_state', None)
                    contact_person_data.append(contact_person_dict)
            request.session['contact_person'] = contact_person_data
            request.session.modified = True
            return redirect('credit_card_view')
    else:
        forms = [ContactPersonForm(prefix=str(i), initial=existing_contact_persons[i-1] if i <= len(existing_contact_persons) else None) for i in range(1, 4)]
        forms[0].fields['first_name'].required = True
        forms[0].fields['last_name'].required = True
        forms[0].fields['mobile_number'].required = True
        forms[0].fields['email_address'].required = True

    context = {
        'forms': forms,
    }
    return render(request, 'registration/contact_person.html', context)

@form_step_required('contact_person', 'contact_person_view')
def credit_card_view(request):
    existing_credit_cards = request.session.get('credit_card', [])

    if request.method == 'POST':
        forms = [CreditCardForm(request.POST, prefix=str(i)) for i in range(1, 4)]
        if all(form.is_valid() for form in forms):
            credit_card_data = []
            for form in forms:
                if form.has_changed():
                    credit_card = form.save(commit=False)
                    credit_card.business = BusinessDetail.objects.last()
                    credit_card_dict = credit_card.__dict__.copy()
                    credit_card_dict.pop('_state', None)
                    credit_card_data.append(credit_card_dict)
            request.session['credit_card'] = credit_card_data
            request.session.modified = True
            return redirect('review_application')
    else:
        forms = [CreditCardForm(prefix=str(i), initial=existing_credit_cards[i-1] if i <= len(existing_credit_cards) else None) for i in range(1, 4)]

    context = {
        'forms': forms,
    }
    return render(request, 'registration/credit_card.html', context)


def review_application(request):
    business_details = request.session.get('business_details', {})
    contact_persons = request.session.get('contact_person', [])
    credit_cards = request.session.get('credit_card', [])

    context = {
        'business_details': business_details,
        'contact_persons': contact_persons,
        'credit_cards': credit_cards,
    }

    return render(request, 'registration/review_application.html', context)

def generate_unique_reference():
    while True:
        reference = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        if not BusinessDetail.objects.filter(reference_number=reference).exists():
            return reference

def final_submission_view(request):
    if request.method == 'POST':
        if 'business_details' in request.session and 'contact_person' in request.session and 'credit_card' in request.session:
            business_details_data = request.session.pop('business_details')
            contact_person_data = request.session.pop('contact_person')
            credit_card_data = request.session.pop('credit_card')

            reference_number = generate_unique_reference()
            business_details_data['reference_number'] = reference_number

            file_fields = ['registration_certificate', 'trading_license', 'tax_compliance_certificate']
            file_data = {field: business_details_data.pop(field) for field in file_fields if field in business_details_data}

            business_detail = BusinessDetail.objects.create(**business_details_data)

            for file_field, temp_file_path in file_data.items():
                if temp_file_path:
                    with default_storage.open(temp_file_path, 'rb') as file:
                        getattr(business_detail, file_field).save(os.path.basename(temp_file_path), File(file), save=True)

            for contact_person in contact_person_data:
                ContactPerson.objects.create(business=business_detail, **contact_person)

            for credit_card in credit_card_data:
                CreditCard.objects.create(business=business_detail, **credit_card)

            if 'contact_person' in request.session:
                del request.session['contact_person']
            if 'credit_card' in request.session:
                del request.session['credit_card']

            return JsonResponse({'reference_number': reference_number})

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