from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.core.exceptions import ValidationError

class Plan(models.Model):
    name=models.CharField(max_length=100, unique=True)
    description=models.TextField(help_text="Description of the plan")
    price=models.DecimalField(max_digits=10, decimal_places=2)
    duration=models.CharField(max_length=50)
    features=models.TextField(help_text="List of features included in the plan")
    # is_popular=models.BooleanField(default=False, help_text="Is this plan popular?")

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    """Extended user profile with user type and additional information"""
    
    USER_TYPES = [
        ('advertiser', 'Advertiser'),
        ('creator', 'Creator'),
        ('guest', 'Guest'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='guest')
    bio = models.TextField(blank=True, null=True)
    tiktok_handle = models.CharField(max_length=100, blank=True, null=True)
    total_views = models.IntegerField(default=0)
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.user_type}"
    
    def calculate_earnings(self):
        """Calculate earnings based on views using fixed rate of 100 Rs per 1000 views"""
        return (self.total_views / 1000) * 100

class Campaign(models.Model):
    """Campaign model for advertisers to create campaigns"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('draft', 'Draft'),
    ]
    
    advertiser = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='campaigns')
    title = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.TextField()
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def get_applications_count(self):
        return self.applications.count()
    
    def get_remaining_budget(self):
        """Calculate remaining budget by subtracting total earnings from approved applications"""
        total_spent = self.applications.filter(status='approved').aggregate(
            total=models.Sum('earnings')
        )['total'] or Decimal('0.00')
        return self.budget - total_spent
    
    def can_pay_earnings_increase(self, current_earnings, new_earnings):
        """Check if campaign budget can accommodate earnings increase"""
        if new_earnings <= current_earnings:
            return True  # No increase, always allowed
        
        earnings_increase = new_earnings - current_earnings
        remaining_budget = self.get_remaining_budget()
        return remaining_budget >= earnings_increase
    
    def decrease_budget_by_earnings_increase(self, current_earnings, new_earnings):
        """Decrease campaign budget by the earnings increase amount"""
        if new_earnings > current_earnings:
            earnings_increase = new_earnings - current_earnings
            if self.can_pay_earnings_increase(current_earnings, new_earnings):
                self.budget = self.budget - earnings_increase
                self.save()
                return True
        return False

class Application(models.Model):
    """Application model for creators to apply for campaigns"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='applications')
    creator = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='applications')
    proposal = models.TextField()
    estimated_views = models.IntegerField(validators=[MinValueValidator(0)])
    estimated_earnings = models.DecimalField(max_digits=10, decimal_places=2)
    # Add actual views and earnings tracking
    views = models.IntegerField(default=0)
    earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.creator.user.username} - {self.campaign.title}"
    
    def save(self, *args, **kwargs):
        """Calculate estimated earnings before saving using fixed rate of 100 Rs per 1000 views"""
        if self.estimated_views:
            self.estimated_earnings = Decimal(self.estimated_views) / Decimal('1000') * Decimal('100')
        super().save(*args, **kwargs)

    def calculate_earnings(self):
        """Calculate actual earnings from actual views using fixed rate of 100 Rs per 1000 views"""
        if self.views > 0:
            return Decimal(self.views) / Decimal('1000') * Decimal('100')
        return Decimal('0.00')
    
    def update_views_and_earnings(self, new_views):
        """Update views and earnings with budget validation"""
        if new_views < 0:
            raise ValidationError("Views must be non-negative")
        
        if self.status != 'approved':
            raise ValidationError("Can only update views for approved applications")
        
        old_earnings = self.earnings
        new_earnings = Decimal(new_views) / Decimal('1000') * Decimal('100')
        
        # Check if campaign budget can accommodate the earnings increase
        if not self.campaign.can_pay_earnings_increase(old_earnings, new_earnings):
            raise ValidationError("Campaign budget insufficient to pay the earnings increase")
        
        # Update views and earnings
        self.views = new_views
        self.earnings = new_earnings
        self.save()
        
        # Decrease campaign budget by the earnings increase
        self.campaign.decrease_budget_by_earnings_increase(old_earnings, new_earnings)
        
        return self.earnings

class Content(models.Model):
    """Content model to track TikTok content and views"""
    creator = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='contents')
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='contents', null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    views = models.IntegerField(default=0)
    earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.creator.user.username}"
    
    def calculate_earnings(self):
        """Calculate earnings based on views using fixed rate of 100 Rs per 1000 views"""
        if self.views > 0:
            return Decimal(self.views) / Decimal('1000') * Decimal('100')
        return Decimal('0.00')

