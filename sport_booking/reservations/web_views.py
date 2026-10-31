from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .domain import ReservationError, TimeInterval
from .services import AvailabilityQueries
from .wiring import build_portal_queries, build_service


class RegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ('username',)


class BookingForm(forms.Form):
    resource_id = forms.TypedChoiceField(
        label='Sportoviště',
        coerce=int,
        choices=(),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    starts_at = forms.DateTimeField(
        label='Začátek',
        input_formats=('%Y-%m-%dT%H:%M',),
        widget=forms.DateTimeInput(
            format='%Y-%m-%dT%H:%M',
            attrs={'type': 'datetime-local', 'class': 'form-control'},
        ),
    )
    ends_at = forms.DateTimeField(
        label='Konec',
        input_formats=('%Y-%m-%dT%H:%M',),
        widget=forms.DateTimeInput(
            format='%Y-%m-%dT%H:%M',
            attrs={'type': 'datetime-local', 'class': 'form-control'},
        ),
    )

    def __init__(self, *args, resources, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['resource_id'].choices = [
            (resource.id, f'{resource.name} · {resource.location}')
            for resource in resources if resource.is_available
        ]


def home(request):
    portal = build_portal_queries()
    resources = portal.resources()
    form = BookingForm(request.POST or None, resources=resources)
    availability_result = None

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.info(request, 'Přihlaste se, prosím, pro vytvoření rezervace.')
            return redirect('login')
        if form.is_valid():
            action = request.POST.get('action')
            if action not in ('availability', 'create'):
                messages.error(request, 'Vyberte kontrolu dostupnosti nebo vytvoření žádosti.')
                return redirect('home')
            service = build_service()
            try:
                actor = service.identity.authenticate(request.user)
                if action == 'availability':
                    availability = AvailabilityQueries(service.store_factory, service.rules)
                    is_available = availability.check(
                        form.cleaned_data['resource_id'],
                        TimeInterval(
                            form.cleaned_data['starts_at'],
                            form.cleaned_data['ends_at'],
                        ),
                    )
                    availability_result = 'available' if is_available else 'unavailable'
                else:
                    reservation = service.create(
                        form.cleaned_data['resource_id'],
                        TimeInterval(
                            form.cleaned_data['starts_at'],
                            form.cleaned_data['ends_at'],
                        ),
                        actor,
                    )
                    messages.success(
                        request,
                        f'Žádost #{reservation.id} je vytvořená. Potvrďte ji níže.',
                    )
                    return redirect('home')
            except ReservationError as error:
                messages.error(request, _error_message(error))

    reservations = (
        portal.reservations_for_user(request.user.pk)
        if request.user.is_authenticated else []
    )
    pending = (
        portal.pending_reservations()
        if request.user.is_authenticated and request.user.is_staff else []
    )
    now = timezone.now()
    return render(request, 'reservations/home.html', {
        'form': form,
        'resources': resources,
        'reservations': reservations,
        'pending_reservations': pending,
        'now': now,
        'availability_result': availability_result,
    })


@require_POST
def reservation_action(request, reservation_id, action):
    service = build_service()
    try:
        actor = service.identity.authenticate(request.user)
        if action == 'confirm':
            reservation = service.confirm(reservation_id, actor)
            if reservation.status == 'PENDING_APPROVAL':
                messages.success(request, 'Žádost čeká na schválení správce.')
            else:
                messages.success(request, 'Rezervace je potvrzená.')
        elif action == 'cancel':
            service.cancel(reservation_id, actor)
            messages.success(request, 'Rezervace byla zrušena.')
        elif action in ('approve', 'reject'):
            reservation = service.approve(
                reservation_id, actor, decision=action,
            )
            messages.success(
                request,
                'Žádost byla schválena.' if action == 'approve'
                else 'Žádost byla zamítnuta.',
            )
        else:
            messages.error(request, 'Požadovaná akce není platná.')
    except ReservationError as error:
        messages.error(request, _error_message(error))
    return redirect('home')


def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Účet je vytvořený. Vítejte!')
        return redirect('home')
    return render(request, 'registration/register.html', {'form': form})


class PortalLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True


class PortalLogoutView(LogoutView):
    next_page = '/'


def _error_message(error):
    messages_by_code = {
        'unauthenticated': 'Pro pokračování se přihlaste.',
        'forbidden': 'Tato akce je dostupná pouze správci sportoviště.',
        'not_found': 'Požadované sportoviště nebo rezervace nebyly nalezeny.',
        'invalid_input': 'Zadané údaje nejsou platné.',
        'invalid_interval': (
            'Zkontrolujte termín: musí být platný, nejvýše 30 dní dopředu '
            'a nesmí přesáhnout 2 hodiny.'
        ),
        'conflict': 'Tuto změnu nelze provést. Ověřte stav rezervace a dostupnost.',
        'expired': 'Žádost o schválení již vypršela.',
    }
    return messages_by_code.get(error.code, 'Akci se nepodařilo dokončit.')
