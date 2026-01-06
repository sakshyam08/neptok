from django.urls import path
from . import views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('guest-login/', views.guest_login, name='guest_login'),
    path('campaigns/', views.campaigns, name='campaigns'),
    
    # Dashboard pages
    path('dashboard/', views.dashboard, name='dashboard'),
    path('advertiser-dashboard/', views.advertiser_dashboard, name='advertiser_dashboard'),
    path('creator-dashboard/', views.creator_dashboard, name='creator_dashboard'),
    
    #Application management
    path('my-applications/', views.my_applications, name='my_applications'),
    path('advertiser/applications/', views.advertiser_applications, name='advertiser_applications'),

    #  path('api/khalti-payout/', KhaltiPayoutView(), name='khalti-payout'),
    #Payment management
    path('get-withdraw/', views.withdraw_page, name='get_withdraw'),
    path('verify-khalti-payment/', views.verify_khalti_payment, name='verify_khalti_payment'),

    #carousel
    path('carousel/', views.carousel, name='carousel'),
    path('explore/', views.Plans, name='explore'),



    
    # Campaign management
    path('create-campaign/', views.create_campaign, name='create_campaign'),
    path('campaign/<int:campaign_id>/', views.campaign_detail, name='campaign_detail'),
    path('apply-campaign/<int:campaign_id>/', views.apply_campaign, name='apply_campaign'),
    
    # Content management
    path('add-content/', views.add_content, name='add_content'),
    path('update-views/<int:content_id>/', views.update_views, name='update_views'),
    path('update-application-views/<int:application_id>/', views.update_application_views, name='update_application_views'),
    path('verify-khalti-payment/', views.verify_khalti_payment, name='verify_khalti_payment'),
] 