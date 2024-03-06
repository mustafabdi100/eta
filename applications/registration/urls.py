from django.urls import path
from .views import business_detail_view, contact_person_view, credit_card_view,review_application,final_submission_view,submission_success_view,dashboard_view,application_review_view,approved_applications_view,rejected_applications_view,reject_application,pending_applications_view,view_activity_logs
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
  
     path('', business_detail_view, name='home'),
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'), 
    path('register/business/', business_detail_view, name='business_detail_view'),
    path('register/contact_person/', contact_person_view, name='contact_person_view'),
     path('register/credit_card/', credit_card_view, name='credit_card_view'),
     path('register/review/', review_application, name='review_application'),
     path('register/final_submission/', final_submission_view, name='final_submission_view'),
    path('register/submission_success/<str:reference_number>/', submission_success_view, name='submission_success'),
    path('dashboard/', dashboard_view, name='dashboard_view'),
    path('application_review/<int:application_id>/', application_review_view, name='application_review_view'),
    path('pending_applications/',pending_applications_view, name='pending_applications_view'),
     path('approved_applications/', approved_applications_view, name='approved_applications_view'),
    path('rejected_applications/', rejected_applications_view, name='rejected_applications_view'),
    # Add a path for rejecting an application directly from the approved list
    path('reject_application/<int:application_id>/', reject_application, name='reject_application'),
    path('activity-logs/', view_activity_logs, name='view_activity_logs'),
    

   
]
