from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count
from django.core.exceptions import ValidationError
import requests
from .models import UserProfile, Campaign, Application, Content
from .forms import UserProfileForm, CampaignForm, ApplicationForm, ContentForm
import json
from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt
from .models import Plan


#Replace with your khalti secret key
KHALTI_SECRET_KEY="YOUR_SECRET_KEY"
KHALTI_VERIFY_URL="https://khalti.com/api/v2/epayment/"

def home(request):
    """Home page with platform introduction"""
    return render(request, 'main/home.html')

def withdraw_page(request):
    return render(request, 'main/withdraw.html')

def login_view(request):
    """Login view with guest login option"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'main/login.html')

def register_view(request):
    """Registration view for new users"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        profile_form = UserProfileForm(request.POST)
        
        if form.is_valid() and profile_form.is_valid():
            user = form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserCreationForm()
        profile_form = UserProfileForm()
    
    return render(request, 'main/register.html', {
        'form': form,
        'profile_form': profile_form
    })

def logout_view(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

def guest_login(request):
    """Guest login for view-only access"""
    # Create a temporary guest session
    request.session['guest_mode'] = True
    messages.info(request, 'You are now browsing as a guest.')
    return redirect('campaigns')

@login_required
def my_applications(request):
    applications = Application.objects.filter(creator=request.user.userprofile)

    
    if request.method == 'POST':
        app_id = request.POST.get('application_id')
        action = request.POST.get('action')  # "accept" or "decline"
        application = get_object_or_404(Application, id=app_id, creator=request.user.userprofile)
        if action == 'accept':
            application.status = 'accepted'
        elif action == 'decline':
            application.status = 'declined'
        application.save()
        return redirect('my_applications')  # redirect to same page after response

    return render(request, 'main/my_applications.html', {'applications': applications})

@login_required
def advertiser_applications(request):
    profile = request.user.userprofile
    if profile.user_type != 'advertiser':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Get all applications related to this advertiser's campaigns
    applications = Application.objects.filter(campaign__advertiser=profile).order_by('-applied_at')
    
    if request.method == 'POST':
        app_id = request.POST.get('application_id')
        action = request.POST.get('action')  # "approve" or "reject"
        application = get_object_or_404(Application, id=app_id, campaign__advertiser=profile)
        
        if action == 'approve':
            application.status = 'approved'
        elif action == 'reject':
            application.status = 'rejected'
        application.save()
        return redirect('advertiser_applications')
    
    return render(request, 'main/advertiser_applications.html', {'applications': applications})


@login_required
def dashboard(request):
    """Main dashboard - redirects based on user type"""
    try:
        profile = request.user.userprofile
        if profile.user_type == 'advertiser':
            return redirect('advertiser_dashboard')
        elif profile.user_type == 'creator':
            return redirect('creator_dashboard')
        else:
            return redirect('campaigns')
    except UserProfile.DoesNotExist:
        # Create profile if it doesn't exist
        profile = UserProfile.objects.create(user=request.user, user_type='guest')
        return redirect('campaigns')

@login_required
def advertiser_dashboard(request):
    """Dashboard for advertisers"""
    try:
        profile = request.user.userprofile
        if profile.user_type != 'advertiser':
            messages.error(request, 'Access denied. Advertiser account required.')
            return redirect('dashboard')
        
        campaigns = Campaign.objects.filter(advertiser=profile).order_by('-created_at')
        total_campaigns = campaigns.count()
        active_campaigns = campaigns.filter(status='active').count()
        total_applications = Application.objects.filter(campaign__advertiser=profile).count()
        
        context = {
            'profile': profile,
            'campaigns': campaigns,
            'total_campaigns': total_campaigns,
            'active_campaigns': active_campaigns,
            'total_applications': total_applications,
        }
        return render(request, 'main/advertiser_dashboard.html', context)
    except UserProfile.DoesNotExist:
        messages.error(request, 'Profile not found.')
        return redirect('home')

@login_required
def creator_dashboard(request):
    """Dashboard for creators"""
    try:
        profile = request.user.userprofile
        if profile.user_type != 'creator':
            messages.error(request, 'Access denied. Creator account required.')
            return redirect('dashboard')
        
        applications = Application.objects.filter(creator=request.user.userprofile)
        contents = Content.objects.filter(creator=profile).order_by('-created_at')
        
        # Calculate total earnings from both content and applications using the new formula
        content_earnings = sum(content.calculate_earnings() for content in contents)
        application_earnings = sum(app.calculate_earnings() for app in applications)
        total_earnings = content_earnings + application_earnings
        
        # Calculate total views from both content and applications
        content_views = contents.aggregate(Sum('views'))['views__sum'] or 0
        application_views = applications.aggregate(Sum('views'))['views__sum'] or 0
        total_views = content_views + application_views
        
        context = {
            'profile': profile,
            'applications': applications,
            'contents': contents,
            'total_earnings': total_earnings,
            'total_views': total_views,
        }
        return render(request, 'main/creator_dashboard.html', context)
    except UserProfile.DoesNotExist:
        messages.error(request, 'Profile not found.')
        return redirect('home')

def carousel(request):
    return render(request, 'main/carousel.html')

# def explore(request):
     
#      return render(request, 'main/explore.html')

def Plans(request):
    plans=Plan.objects.all()
    return render(request,'main/explore.html',{'plans':plans})

def campaigns(request):
    """Public campaigns page"""
    campaigns = Campaign.objects.filter(is_public=True, status='active').order_by('-created_at')
    
    # Check if user is logged in and has a profile
    user_profile = None
    if request.user.is_authenticated:
        try:
            user_profile = request.user.userprofile
        except UserProfile.DoesNotExist:
            pass
    
    context = {
        'campaigns': campaigns,
        'user_profile': user_profile,
        'is_guest': request.session.get('guest_mode', False)
    }
    return render(request, 'main/campaigns.html', context)

@login_required
def create_campaign(request):
    """Create new campaign (advertisers only)"""
    try:
        profile = request.user.userprofile
        if profile.user_type != 'advertiser':
            messages.error(request, 'Only advertisers can create campaigns.')
            return redirect('dashboard')
        
        if request.method == 'POST':
            form = CampaignForm(request.POST)
            if form.is_valid():
                campaign = form.save(commit=False)
                campaign.advertiser = profile
                campaign.save()
                messages.success(request, 'Campaign created successfully!')
                return redirect('advertiser_dashboard')
        else:
            form = CampaignForm()
        
        return render(request, 'main/create_campaign.html', {'form': form})
    except UserProfile.DoesNotExist:
        messages.error(request, 'Profile not found.')
        return redirect('home')

@login_required
def apply_campaign(request, campaign_id):
    """Apply for a campaign (creators only)"""
    try:
        profile = request.user.userprofile
        if profile.user_type != 'creator':
            messages.error(request, 'Only creators can apply for campaigns.')
            return redirect('campaigns')
        
        campaign = get_object_or_404(Campaign, id=campaign_id, is_public=True)
        
        # Check if already applied
        if Application.objects.filter(creator=profile, campaign=campaign).exists():
            messages.warning(request, 'You have already applied for this campaign.')
            return redirect('campaigns')
        
        if request.method == 'POST':
            form = ApplicationForm(request.POST)
            if form.is_valid():
                application = form.save(commit=False)
                application.creator = profile
                application.campaign = campaign
                application.save()
                messages.success(request, 'Application submitted successfully!')
                return redirect('creator_dashboard')
        else:
            form = ApplicationForm()
        
        return render(request, 'main/apply_campaign.html', {
            'form': form,
            'campaign': campaign
        })
    except UserProfile.DoesNotExist:
        messages.error(request, 'Profile not found.')
        return redirect('home')

@login_required
def add_content(request):
    """Add new content (creators only)"""
    try:
        profile = request.user.userprofile
        if profile.user_type != 'creator':
            messages.error(request, 'Only creators can add content.')
            return redirect('dashboard')
        
        if request.method == 'POST':
            form = ContentForm(request.POST)
            if form.is_valid():
                content = form.save(commit=False)
                content.creator = profile
                content.save()
                messages.success(request, 'Content added successfully!')
                return redirect('creator_dashboard')
        else:
            form = ContentForm()
        
        return render(request, 'main/add_content.html', {'form': form})
    except UserProfile.DoesNotExist:
        messages.error(request, 'Profile not found.')
        return redirect('home')

def campaign_detail(request, campaign_id):
    """Campaign detail view - accessible to all users"""
    campaign = get_object_or_404(Campaign, id=campaign_id, is_public=True)
    
    # Check if user is logged in and has a profile
    user_profile = None
    if request.user.is_authenticated:
        try:
            user_profile = request.user.userprofile
        except UserProfile.DoesNotExist:
            pass
    
    context = {
        'campaign': campaign,
        'user_profile': user_profile,
        'is_guest': request.session.get('guest_mode', False)
    }
    return render(request, 'main/campaign_detail.html', context)



@require_POST
@login_required
def update_views(request, content_id):
    """Update content views and earnings (AJAX)"""
    try:
        content = get_object_or_404(Content, id=content_id, creator__user=request.user)
        data = json.loads(request.body)
        new_views = int(data.get('views', 0))
        
        if new_views >= 0:
            content.views = new_views
            content.earnings = content.calculate_earnings()
            content.save()
            
            # Update creator's total views and earnings from both Content and Application
            profile = request.user.userprofile
            total_content_views = Content.objects.filter(creator=profile).aggregate(Sum('views'))['views__sum'] or 0
            total_content_earnings = Content.objects.filter(creator=profile).aggregate(Sum('earnings'))['earnings__sum'] or 0
            approved_applications = Application.objects.filter(creator=profile, status='approved')
            total_app_views = approved_applications.aggregate(Sum('views'))['views__sum'] or 0
            total_app_earnings = approved_applications.aggregate(Sum('earnings'))['earnings__sum'] or 0
            profile.total_views = total_content_views + total_app_views
            profile.total_earnings = total_content_earnings + total_app_earnings
            profile.save()
            
            return JsonResponse({
                'success': True,
                'views': content.views,
                'earnings': float(content.earnings)
            })
        else:
            return JsonResponse({'success': False, 'error': 'Views must be positive'})
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({'success': False, 'error': 'Invalid data'})
    except Content.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Content not found'})

@require_POST
@login_required
def update_application_views(request, application_id):
    """Update application views and earnings with budget validation (AJAX)"""
    try:
        # Get application and validate ownership
        application = get_object_or_404(Application, id=application_id, creator__user=request.user)

        # Parse request data
        data = json.loads(request.body)
        new_views = int(data.get('views', 0))

        # Validate input
        if new_views < 0:
            return JsonResponse({'success': False, 'error': 'Views must be non-negative'})

        # Validate application status
        if application.status != 'approved':
            return JsonResponse({'success': False, 'error': 'Can only update views for approved applications'})

        # Store old values for comparison
        old_views = application.views
        old_earnings = application.earnings

        # Update views and earnings with budget validation
        try:
            new_earnings = application.update_views_and_earnings(new_views)
        except ValidationError as e:
            return JsonResponse({'success': False, 'error': str(e)})

        # Update creator's total views and earnings from both Content and Application
        profile = request.user.userprofile
        total_content_views = Content.objects.filter(creator=profile).aggregate(Sum('views'))['views__sum'] or 0
        total_content_earnings = Content.objects.filter(creator=profile).aggregate(Sum('earnings'))['earnings__sum'] or 0
        approved_applications = Application.objects.filter(creator=profile, status='approved')
        total_app_views = approved_applications.aggregate(Sum('views'))['views__sum'] or 0
        total_app_earnings = approved_applications.aggregate(Sum('earnings'))['earnings__sum'] or 0
        profile.total_views = total_content_views + total_app_views
        profile.total_earnings = total_content_earnings + total_app_earnings
        profile.save()

        # Get updated campaign budget
        campaign = application.campaign
        remaining_budget = campaign.get_remaining_budget()

        return JsonResponse({
            'success': True,
            'views': application.views,
            'earnings': float(application.earnings),
            'campaign_id': campaign.id,
            'campaign_budget': float(campaign.budget),
            'remaining_budget': float(remaining_budget),
            'earnings_increase': float(new_earnings - old_earnings) if new_earnings > old_earnings else 0.0
        })

    except (ValueError, json.JSONDecodeError):
        return JsonResponse({'success': False, 'error': 'Invalid data format'})
    except Application.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Application not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Unexpected error: {str(e)}'})


@csrf_exempt
def verify_khalti_payment(request):
    if request.method == "POST":
        try:
            payload =json.loads(request.body)

            response = requests.post(
                KHALTI_VERIFY_URL,
                json={
                    'token': payload.get("token"),
                    'amount':payload.get("amount")

                },
                headers={
                    'Authorization':f'Bearer{KHALTI_SECRET_KEY}',
                    'Content-Type':'application/json'
                }
            )
            verification_data = response.json()

            if response.status_code == 200 and verification_data.get('status') == 'success':
                return JsonResponse({"success":True})
            else:
                return JsonResponse({"success":False},status=400)
            
        except Exception as e:
            return JsonResponse({"success":False,"error":str(e)},status=400)
    
    return JsonResponse({"success":False},status=400)
    
    