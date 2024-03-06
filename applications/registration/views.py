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


def business_detail_view(request):
    if request.method == 'POST':
        form = BusinessDetailForm(request.POST, request.FILES)
        if form.is_valid():
            # Call the utility function to ensure the tmp directory exists
            ensure_tmp_directory_exists()

            # Handle non-file fields
            business_data = form.cleaned_data.copy()
            # Temporarily store file uploads and update business_data with file paths
            for file_field in ['registration_certificate', 'trading_license', 'tax_compliance_certificate']:
                if file_field in request.FILES:
                    file = request.FILES[file_field]
                    # Generate a unique filename to avoid overwrite
                    unique_filename = f"{file_field}_{request.session.session_key}_{file.name}"
                    # Save file temporarily
                    path = default_storage.save('tmp/' + unique_filename, ContentFile(file.read()))
                    # Store file path in business_data
                    business_data[file_field] = path

            # Store business details in session
            request.session['business_details'] = business_data

            # Redirect to the next step
            return redirect('contact_person_view')  # Make sure this is the correct URL name for the next step
    else:
        form = BusinessDetailForm()
    return render(request, 'registration/business_detail.html', {'form': form})

def contact_person_view(request):
    if 'contact_persons' not in request.session:
        request.session['contact_persons'] = []

    if request.method == 'POST':
        form = ContactPersonForm(request.POST)
        if form.is_valid():
            contact_person_data = form.cleaned_data
            request.session['contact_persons'].append(contact_person_data)
            request.session.modified = True  # Ensure the session is saved
            
            if 'add_another' in request.POST:
                form = ContactPersonForm()  # Reinitialize the form for a fresh entry
            else:
                # If done adding contact persons, proceed to the next step
                return redirect('credit_card_view')
    else:
        form = ContactPersonForm()  # Initialize an empty form for GET requests
    
    context = {
        'form': form,
        'can_add_more': len(request.session.get('contact_persons', [])) < 3,
        'contact_persons': request.session.get('contact_persons', [])  # Optional: Display already added contacts
    }
    return render(request, 'registration/contact_person.html', context)


def credit_card_view(request):
    if 'credit_cards' not in request.session:
        request.session['credit_cards'] = []

    form = CreditCardForm()  # Initialize an empty form for both GET and POST requests
    if request.method == 'POST':
        form = CreditCardForm(request.POST)
        if form.is_valid():
            credit_card_data = form.cleaned_data
            request.session['credit_cards'].append(credit_card_data)
            request.session.modified = True  # Ensure the session data is updated
            
            if 'add_another' in request.POST:
                return redirect('credit_card_view')  # Redirect back to allow adding another credit card
            else:
                return redirect('review_application')  # Proceed to the review application step if "Review" is clicked
    
    context = {
        'form': form,
        'can_add_more': len(request.session.get('credit_cards', [])) < 3,
        'credit_cards': request.session.get('credit_cards', [])  # Optionally display already added cards
    }
    return render(request, 'registration/credit_card.html', context)



def review_application(request):
    # Fetch data from session
    business_details = request.session.get('business_details', {})
    contact_persons = request.session.get('contact_persons', [])
    credit_cards = request.session.get('credit_cards', [])

    # Context to display the data for review
    context = {
        'business_details': business_details,
        'contact_persons': contact_persons,
        'credit_cards': credit_cards
    }

    return render(request, 'registration/review_application.html', context)


def generate_unique_reference():
    while True:
        reference = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        if not BusinessDetail.objects.filter(reference_number=reference).exists():
            return reference

def final_submission_view(request):
    # Ensure there's data to submit
    if 'business_details' in request.session and 'contact_persons' in request.session and 'credit_cards' in request.session:
        # Retrieve data from session
        business_details_data = request.session.pop('business_details')
        contact_persons_data = request.session.pop('contact_persons')
        credit_cards_data = request.session.pop('credit_cards')

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

        # Create ContactPerson instances
        for cp_data in contact_persons_data:
            ContactPerson.objects.create(business=business_detail, **cp_data)

        # Create CreditCard instances
        for cc_data in credit_cards_data:
            CreditCard.objects.create(business=business_detail, **cc_data)

        # Clear session data for contact persons and credit cards to prevent re-use
        if 'contact_persons' in request.session:
            del request.session['contact_persons']
        if 'credit_cards' in request.session:
            del request.session['credit_cards']

        # Redirect to a success page with the reference number
        return redirect('submission_success', reference_number=reference_number)
        

    # If there's no data in the session (e.g., direct access), redirect to the start of the form process
    return redirect('business_detail_view')


def submission_success_view(request, reference_number):
    context = {'reference_number': reference_number}
    return render(request, 'registration/submission_success.html', context)

@login_required
def dashboard_view(request):
    total_applications = BusinessDetail.objects.count()
    pending_applications = BusinessDetail.objects.filter(status='pending').count()
    approved_applications = BusinessDetail.objects.filter(status='approved').count()
    rejected_applications = BusinessDetail.objects.filter(status='rejected').count()
    all_applications = BusinessDetail.objects.all()
    context = {
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'approved_applications': approved_applications,
        'rejected_applications': rejected_applications,
        'all_applications': all_applications,
    }
    return render(request, 'registration/dashboard.html', context)

@login_required
def pending_applications_view(request):
    pending_applications = BusinessDetail.objects.filter(status='pending')
    return render(request, 'registration/pending_applications.html', {'pending_applications': pending_applications})

@login_required
def approved_applications_view(request):
    approved_applications = BusinessDetail.objects.filter(status='approved')
    return render(request, 'registration/approved_applications.html', {'approved_applications': approved_applications})

@login_required
def rejected_applications_view(request):
    rejected_applications = BusinessDetail.objects.filter(status='rejected')
    return render(request, 'registration/rejected_applications.html', {'rejected_applications': rejected_applications})

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