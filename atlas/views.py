from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, ListView
from django.core.exceptions import ObjectDoesNotExist

from django.core.paginator import Paginator
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger

from alumni.models import Alumni, Address

from alumni.fields import CollegeField, ClassField, MajorField, DegreeField, IndustryField, JobField, CountryField

from django.shortcuts import redirect
from django.urls import reverse

# Create a new SearchFilter instance
from registry.search.filter import SearchFilter, ParsingError
search = SearchFilter({
    'city': 'address__city',
    'country': 'address__country',
    'class': 'jacobs__graduation',
    'college': 'jacobs__college',
    'major': 'jacobs__major',
    'degree': 'jacobs__degree',
    'industry': 'job__industry',
    'job': 'job__job',
}, [
    'firstName', 'lastName', 'address__city',
    'jacobs__degree',
    'skills__otherDegrees', 'skills__spokenLanguages', 'skills__programmingLanguages', 'skills__areasOfInterest',
    'job__employer', 'job__position',
    'atlas__secret',
])

ADVANCED_SEARCH_FIELDS = [
    ['college', 'College', CollegeField.CHOICES],
    ['class', 'Class', ClassField.CHOICES],
    ['major', 'Major', MajorField.CHOICES],
    ['degree', 'Degree', DegreeField.CHOICES],
    ['industry', 'Industry', IndustryField.CHOICES],
    ['job', 'Job', JobField.CHOICES],
    ['country', 'Country', CountryField.COUNTRY_CHOICES]
]


def can_view_atlas(user):
    """ Function that checks if access to atlas functionality is available """
    if not user.is_authenticated:
        return False

    # for non-admins, i.e. user that are neither staff nor superadmin
    if not user.is_staff and not user.is_superuser:

        # we need to make sure that they have been approved before they
        # can view this page.
        try:
            approval = user.alumni.approval
            if not approval.approval:
                return False
        except ObjectDoesNotExist:
            return False

        # we need to make sure that they have chosen to be included in the
        return user.alumni.atlas.included

    return True


def make_pagination_ui_ctx(page):
    """ Computes the layout of the pagination UI element """
    context = {}

    # 1 ... p c n ... l
    p = page.has_previous() and page.previous_page_number()
    c = page.number
    n = page.has_next() and page.next_page_number()
    l = page.paginator.num_pages

    # Start figuring out if we need the one and the dots
    if not p or p == 1:
        print1 = False
        print1Dots = False
    elif p == 2:
        print1 = True
        print1Dots = False
    else:
        print1 = True
        print1Dots = True

    context['print1'] = print1
    context['print1Dots'] = print1Dots

    # End by figuring out if we need the last tods etc
    if not n or n == l:
        printL = False
        printLDots = False
    elif n == l - 1:
        printL = True
        printLDots = False
    else:
        printL = True
        printLDots = True

    context['printL'] = printL
    context['printLDots'] = printLDots

    return context


@method_decorator(login_required, name='dispatch')
class HomeView(TemplateView):
    template_name = 'atlas/index.html'

    def get_template_names(self):
        if not can_view_atlas(self.request.user):
            return 'atlas/denied.html'
        return 'atlas/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_fields'] = ADVANCED_SEARCH_FIELDS

        coords = map(lambda x: '[{}, {}]'.format(
            x[0], x[1]), Address.all_valid_coords())
        context['people_coords'] = '[{}]'.format(','.join(coords))

        return context


@method_decorator(login_required, name='dispatch')
class ProfileView(TemplateView):
    template_name = 'atlas/profile.html'

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)
        # Find the user with the given id and approved approval
        context['alumni'] = get_object_or_404(
            Alumni, profile__id=kwargs['id'], approval__approval=True, atlas__included=True)
        coords = context['alumni'].address.coords
        context['alumni_coords'] = '[{}, {}]'.format(coords[0], coords[1])

        return context

    def get(self, request, *args, **kwargs):
        if not can_view_atlas(request.user):
            raise Http404
        return super(ProfileView, self).get(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class SearchView(ListView):
    model = Alumni
    template_name = "atlas/search.html"
    paginate_by = 10

    def get_context_data(self, **kwargs):

        # Get the context from the parent
        context = super(SearchView, self).get_context_data(**kwargs)
        context['search_fields'] = ADVANCED_SEARCH_FIELDS

        # Read out the query
        query = self.request.GET.get('query') or ''
        context['query'] = query

        # Read out the page number
        page = self.request.GET.get('page')

        # build a query
        # and also build a search
        queryset = Alumni.objects.filter(
            approval__approval=True, atlas__included=True)
        q, err = search(queryset, query)

        # If we had an error, raise it
        if err is not None:
            if isinstance(err, ParsingError):
                context['error'] = err.message
                return context

            raise err

        paginator = Paginator(queryset.filter(
            q).order_by('lastName'), self.paginate_by)

        try:
            page = paginator.page(page)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)

        context['page'] = page
        context['pagination'] = make_pagination_ui_ctx(page)

        return context

    def get(self, request, *args, **kwargs):
        if not can_view_atlas(request.user):
            raise Http404

        # if there is no search, redirect to home
        if not self.request.GET.get('query', '').strip():
            return redirect(reverse('atlas_home'))

        return super(SearchView, self).get(request, *args, **kwargs)
