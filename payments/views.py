import stripe
from payments import stripewrapper

from datetime import datetime
from raven.contrib.django.raven_compat.models import client

from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import formats
from django.utils.decorators import method_decorator
from django.views.generic import FormView, TemplateView

from .forms import MembershipInformationForm, PaymentMethodForm
from .models import MembershipInformation, SubscriptionInformation
from .plans import subscription_plans

from alumni.fields import PaymentTypeField

from registry.decorators import require_setup_completed, require_unset_component
from registry.views.registry import default_alternative
from registry.views.setup import SetupComponentView

class SignupView(SetupComponentView):
    setup_name = 'Tier Selection'
    setup_subtitle = 'How much do you want to support us?'
    setup_form_class = MembershipInformationForm

    template_name = 'payments/tier.html'

    def form_valid(self, form):

        # Create the stripe customer
        customer, err = stripewrapper.create_customer(self.request.user.alumni)
        if err is not None:
            form.add_error(None, 'Something went wrong when talking to our payment service provider. Please try again later or contact support. ')
            return None
        
        # store the information
        instance = form.save(commit=False)
        instance.member = self.request.user.alumni
        instance.customer = customer.id
        instance.save()

        # if we selected the starter tier, create subscription information now
        if instance.tier == 'st':
            SubscriptionInformation.create_starter_subscription(self.request.user.alumni)

        return instance

class SubscribeView(SetupComponentView):
    setup_name = 'Payment Details'
    setup_subtitle = ''
    setup_form_class = PaymentMethodForm
    
    template_name = 'payments/subscribe.html'

    @classmethod
    def setup_class(cls):
        return SubscriptionInformation

    template_name = 'payments/subscribe.html'

    def form_valid(self, form):
        # Attach the payment source to the customer
        customer = self.request.user.alumni.payment.customer
        _, err = form.attach_to_customer(customer)

        # if the error is not, return
        if err is not None:
            form.add_error(None, 'Something went wrong when talking to our payment service provider. Please try again later or contact support. ')
            return None

        # grab tier and plan        
        tier = self.request.user.alumni.payment.tier
        plan = subscription_plans[tier].stripe_id

        # create a subscription on the plan
        sub, err = stripewrapper.create_subscription(customer, plan)
        if err is not None:
            form.add_error(None, 'Something went wrong trying to create the subscription. Please try again later or contact support. ')
            return None
        
        # Create the object
        instance = SubscriptionInformation.objects.create(
            member = self.request.user.alumni,
            tier = tier,
            subscription = sub.id,
            start = datetime.now()
        )

        return instance

class PaymentsTableMixin:
    @classmethod
    def format_datetime(cls, epoch, format="DATETIME_FORMAT"):
        """ Formats seconds since epoch as a readable date """
        date_joined = datetime.fromtimestamp(epoch)
        return formats.date_format(date_joined, format)
    
    @classmethod
    def format_description(cls, line):
        """ Formats the description line of an invoice """
        # if we have a description, return it
        if line.description is not None:
            return line.description

        # if we have a subscription show {{Name}} x timeframe
        if line.type == "subscription":
            name = "{} ({} - {})".format(line.plan.name,
                                        cls.format_datetime(line.period.start,
                                                        "DATE_FORMAT"),
                                        cls.format_datetime(line.period.end,
                                                        "DATE_FORMAT"))
            return "{} x {}".format(line.quantity, name)

        # we have a normal line item, and there should have been a description
        else:
            raise Exception("Non-subscription without description")
    @classmethod
    def format_total(cls, amount, cur):
        """ Formats the total """
        if cur == "eur":
            return "%0.2f €" % (amount / 100)
        elif cur == "usd":
            return "%0.2f $" % (amount / 100)
        else:
            raise Exception("unknown currency {}".format(cur))

    @classmethod
    def get_invoice_table(cls, customer):
        invoices, err = stripewrapper.get_payment_table(customer)

        if err is not None:
            try:
                invoices = [{
                    'lines': [cls.format_description(l) for l in iv['lines']],
                    'date': cls.format_datetime(iv['date']),
                    'total': cls.format_total(iv['total'][0], iv['total'][1]),
                    'paid': iv['paid'],
                    'closed': iv['closed']
                } for iv in invoices]
            except Exception as e:
                err = e
        
        if err is not None:
            err = 'Something went wrong. Please try again later or contact support. '
        
        return invoices, err    

@method_decorator(require_setup_completed(default_alternative), name='dispatch')
class PaymentsView(PaymentsTableMixin, TemplateView):
    template_name = 'payments/view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        (invoices, error) = self.__class__.get_invoice_table(self.request.user.alumni.payment.customer)

        context.update({
            'invoices': invoices,
            'error': error
        })

        return context

@method_decorator(user_passes_test(lambda u: u.is_superuser), name='dispatch')
class PaymentsAdminView(PaymentsTableMixin, TemplateView):
    template_name = 'payments/view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        payment = get_object_or_404(MembershipInformation,
                                member__profile__id=kwargs['id'])

        (invoices, error) = self.__class__.get_invoice_table(payment.customer)

        context.update({
            'admin': True,
            'username': payment.member.profile.username,
            'invoices': invoices,
            'error': error
        })

        return context