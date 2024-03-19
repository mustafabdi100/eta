from django.db import models
from django.contrib.auth.models import User
from .validators import validate_file_extension


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)  # Use this field to activate/deactivate users

    def __str__(self):
        return self.user.username

class BusinessDetail(models.Model):
    business_name = models.CharField(max_length=255)
    reference_number = models.CharField(max_length=10, unique=True, blank=True, null=True)
    registration_number = models.CharField(max_length=100)
    kra_pin = models.CharField(max_length=50)
    business_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    phone_code = models.CharField(max_length=10,null=True)
    email_address = models.EmailField()
    registration_certificate = models.FileField(upload_to='documents/', validators=[validate_file_extension])
    trading_license = models.FileField(upload_to='documents/', validators=[validate_file_extension])
    tax_compliance_certificate = models.FileField(upload_to='documents/', validators=[validate_file_extension])
    created_at = models.DateTimeField(auto_now_add=True,null=True)
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    def __str__(self):
        return self.business_name

class ContactPerson(models.Model):
    business = models.ForeignKey(BusinessDetail, related_name='contact_persons', on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=20)
    email_address = models.EmailField()
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class CreditCard(models.Model):
    business = models.ForeignKey(BusinessDetail, related_name='credit_cards', on_delete=models.CASCADE)
    card_type = models.CharField(max_length=50, choices=[('Visa', 'Visa'), ('MasterCard', 'MasterCard'), ('American Express', 'American Express')])
    last_8_digits = models.CharField(max_length=8)
    def __str__(self):
        return f"{self.card_type} - XXXX XXXX XXXX {self.last_8_digits}"
    

class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('submission', 'Submission'),
        ('approval', 'Approval'),
        ('rejection', 'Rejection'),
        ('add_user', 'Add User'),
        ('remove_user', 'Remove User'),
        ('deactivate_user', 'Deactivate User'),
        ('activate_user', 'Activate User'),
        # Add more actions as needed
    ]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    username = models.CharField(max_length=150, blank=True, null=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    deleted_user = models.CharField(max_length=150, blank=True, null=True, help_text="Username of the deleted user, if applicable.")

    
    def save(self, *args, **kwargs):
        if self.user and not self.username:
            self.username = self.user.username
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"

