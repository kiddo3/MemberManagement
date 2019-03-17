"""Registry URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.views.generic import TemplateView, RedirectView

from .views import registry as registry_views
from .views import setup as setup_views
from .views import edit as edit_views
from .views import view as view_views

urlpatterns = [
    # The Portal home page
    url(r'^$', registry_views.home, name='portal'),

    # Static requirements
    url(r'^imprint/$', TemplateView.as_view(template_name="static/imprint.html"), name='imprint'),
    url(r'^privacy/$', RedirectView.as_view(url='https://jacobs-alumni.de/privacy/', permanent=False), name='privacy'),

    # Registration
    url('^register/$', setup_views.register, name='register'),

    # Initial data Setup
    url(r'^setup/$', setup_views.setup, name='setup'),
    url(r'^setup/address/$', setup_views.address, name='setup_address'),
    url(r'^setup/social/$', setup_views.social, name='setup_social'),
    url(r'^setup/jacobs/$', setup_views.jacobs, name='setup_jacobs'),
    url(r'^setup/job/$', setup_views.job, name='setup_job'),
    url(r'^setup/skills/$', setup_views.skills, name='setup_skills'),
    url(r'^setup/atlas/$', setup_views.atlas, name='setup_atlas'),
    url(r'^setup/payment/$', setup_views.SubscribeView.as_safe_view(),
        name='setup_payment'),

    # the portal for the user
    url(r'portal/', registry_views.portal, name='portal'),

    # Edit views
    url(r'^edit/$', edit_views.edit, name='edit'),
    url(r'^edit/address/$', edit_views.address, name='edit_address'),
    url(r'^edit/payments/$', view_views.payments, name='edit_payments'),
    url(r'^edit/payments/(?P<id>\d+)/$',
        view_views.payments_admin, name='view_payments_admin'),
    url(r'^edit/social/$', edit_views.social, name='edit_social'),
    url(r'^edit/jacobs/$', edit_views.jacobs, name='edit_jacobs'),
    url(r'^edit/job/$', edit_views.job, name='edit_job'),
    url(r'^edit/skills/$', edit_views.skills, name='edit_skills'),
    url(r'^edit/atlas/$', edit_views.atlas, name='edit_atlas'),
]
