from datetime import timedelta
from urllib.parse import urlencode

from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .domain import ReservationError, TimeInterval
from .services import AvailabilityQueries
from .rules import TimeRules
from .wiring import build_portal_queries, build_resource_service, build_service


class RegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ('username',)


class OperatingHoursForm(forms.Form):
    opens_at = forms.TimeField(label='Otevřeno od', input_formats=('%H:%M',))
    closes_at = forms.TimeField(label='Otevřeno do', input_formats=('%H:%M',))

    def clean(self):
        data = super().clean()
        if data.get('opens_at') is not None and data.get('closes_at') is not None:
            try:
                TimeRules().validate_operating_hours(data['opens_at'], data['closes_at'])
            except ReservationError:
                raise forms.ValidationError('Čas otevření musí být před časem zavření.')
        return data


class ScheduleFilterForm(forms.Form):
    resource_id = forms.TypedChoiceField(label='Sportoviště', coerce=int, choices=(),
                                        widget=forms.Select(attrs={'class': 'form-control'}))
    schedule_date = forms.DateField(label='Den', widget=forms.DateInput(
        format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'},
    ))

    def __init__(self, *args, resources, now, **kwargs):
        super().__init__(*args, **kwargs)
        self.today = timezone.localdate(now)
        self.fields['resource_id'].choices = [
            (row.id, f'{row.name} · {row.location}') for row in resources if row.is_available
        ]
        self.fields['schedule_date'].widget.attrs.update(
            min=self.today.isoformat(), max=(self.today + timedelta(days=30)).isoformat(),
        )

    def clean_schedule_date(self):
        day = self.cleaned_data['schedule_date']
        if not self.today <= day <= self.today + timedelta(days=30):
            raise forms.ValidationError('Vyberte den od dneška nejvýše 30 dní dopředu.')
        return day


class BookingForm(forms.Form):
    resource_id = forms.TypedChoiceField(
        label='Sportoviště',
        coerce=int,
        choices=(),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    selection_mode = forms.ChoiceField(
        choices=(('slots', 'Vybrat hodinové bloky'), ('manual', 'Zadat přesný čas')),
        required=False, initial='slots', widget=forms.RadioSelect,
    )
    schedule_date = forms.DateField(label='Den rozvrhu', required=False, widget=forms.HiddenInput)
    selected_blocks = forms.MultipleChoiceField(label='Hodinové bloky', required=False, choices=())
    starts_at = forms.DateTimeField(
        required=False,
        label='Začátek',
        input_formats=('%Y-%m-%dT%H:%M',),
        widget=forms.DateTimeInput(
            format='%Y-%m-%dT%H:%M',
            attrs={'type': 'datetime-local', 'class': 'form-control'},
        ),
    )
    ends_at = forms.DateTimeField(
        required=False,
        label='Konec',
        input_formats=('%Y-%m-%dT%H:%M',),
        widget=forms.DateTimeInput(
            format='%Y-%m-%dT%H:%M',
            attrs={'type': 'datetime-local', 'class': 'form-control'},
        ),
    )

    def __init__(self, *args, resources, blocks=(), **kwargs):
        data = args[0] if args else kwargs.get('data')
        if data is not None and data.get('selection_mode') == 'slots':
            data = data.copy()
            # Slot identifiers, not optional client-supplied datetimes, define this interval.
            data['starts_at'] = data['ends_at'] = ''
            if args:
                args = (data, *args[1:])
            else:
                kwargs['data'] = data
        super().__init__(*args, **kwargs)
        self.blocks = list(blocks)
        self.fields['selected_blocks'].choices = [(b.key, b.label) for b in self.blocks if b.available]
        self.fields['resource_id'].choices = [
            (resource.id, f'{resource.name} · {resource.location}')
            for resource in resources if resource.is_available
        ]

    def clean(self):
        data = super().clean()
        mode = data.get('selection_mode') or 'manual'
        if mode == 'manual':
            for field in ('starts_at', 'ends_at'):
                if not data.get(field) and field not in self.errors:
                    self.add_error(field, 'Zadejte datum a čas.')
        else:
            if not data.get('schedule_date'):
                self.add_error('schedule_date', 'Vyberte den rozvrhu.')
            keys = data.get('selected_blocks', [])
            selected = [block for block in self.blocks if block.key in keys]
            if 'selected_blocks' not in self.errors:
                if len(keys) != len(set(keys)) or len(selected) not in (1, 2):
                    self.add_error('selected_blocks', 'Vyberte jeden nebo dva navazující hodinové bloky.')
                elif len(selected) == 2 and (selected[0].end != selected[1].start
                        or timezone.localdate(selected[0].start) != timezone.localdate(selected[1].start)):
                    self.add_error('selected_blocks', 'Vybrané bloky musí bezprostředně navazovat.')
                else:
                    data['starts_at'], data['ends_at'] = selected[0].start, selected[-1].end
        return data


def home(request):
    portal = build_portal_queries()
    resources = portal.resources()
    now = timezone.now()
    available = [row for row in resources if row.is_available]
    default_id = available[0].id if available else ''
    source = request.POST if request.method == 'POST' else request.GET
    filter_data = {
        'resource_id': source.get('resource_id', default_id),
        'schedule_date': source.get('schedule_date') or timezone.localdate(now).isoformat(),
    }
    schedule_filter = ScheduleFilterForm(filter_data, resources=resources, now=now, auto_id='schedule_%s')
    blocks = []
    week = {'days': [], 'rows': [], 'blocks': []}
    if request.user.is_authenticated and schedule_filter.is_valid():
        try:
            week = portal.weekly_schedule(
                schedule_filter.cleaned_data['resource_id'],
                schedule_filter.cleaned_data['schedule_date'], now,
            )
            blocks = week['blocks']
        except ReservationError as error:
            schedule_filter.add_error('resource_id', _error_message(error))
    selected_keys = set(request.POST.getlist('selected_blocks'))
    for row in week['rows']:
        row['cells'] = [
            {'block': block, 'selected': bool(block and block.key in selected_keys)}
            for block in row['cells']
        ]
    week_links = {}
    if week.get('start'):
        today = timezone.localdate(now)
        current_monday = today - timedelta(days=today.weekday())
        for name, target in (('previous', week['start'] - timedelta(days=7)),
                             ('next', week['start'] + timedelta(days=7))):
            if current_monday <= target <= today + timedelta(days=30):
                target = max(target, today)
                week_links[name] = '?' + urlencode({
                    'resource_id': filter_data['resource_id'], 'schedule_date': target.isoformat(),
                }) + '#booking-title'
    form = BookingForm(request.POST or None, resources=resources, blocks=blocks, initial={
        'resource_id': filter_data['resource_id'], 'schedule_date': filter_data['schedule_date'],
    })
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
                        (f'Rezervace #{reservation.id} je potvrzená.'
                         if reservation.status == 'CONFIRMED'
                         else f'Žádost #{reservation.id} čeká na schválení správce.'),
                    )
                    if form.cleaned_data.get('selection_mode') == 'slots':
                        query = urlencode({
                            'resource_id': form.cleaned_data['resource_id'],
                            'schedule_date': timezone.localdate(form.cleaned_data['starts_at']).isoformat(),
                        })
                        return redirect(f'{reverse("home")}?{query}#booking-title')
                    return redirect('home')
            except ReservationError as error:
                messages.error(request, _error_message(error))

    now = timezone.now()
    reservations = (
        portal.reservations_for_user(request.user.pk, now)
        if request.user.is_authenticated else []
    )
    pending = (
        portal.pending_reservations(now)
        if request.user.is_authenticated and request.user.is_staff else []
    )
    return render(request, 'reservations/home.html', {
        'form': form,
        'schedule_filter': schedule_filter,
        'hour_blocks': [(block, block.key in selected_keys) for block in blocks],
        'schedule_week': week,
        'week_links': week_links,
        'selection_mode': request.POST.get('selection_mode', 'manual') if request.method == 'POST' else 'slots',
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
        if action == 'cancel':
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
        'outside_hours': 'Celá rezervace musí být v provozní době sportoviště.',
        'conflict': 'Tuto změnu nelze provést. Ověřte stav rezervace a dostupnost.',
        'expired': 'Žádost o schválení již vypršela.',
    }
    return messages_by_code.get(error.code, 'Akci se nepodařilo dokončit.')


@require_POST
def update_operating_hours(request, resource_id):
    service = build_resource_service()
    try:
        actor = service.identity.authenticate(request.user)
        service.identity.require_approver(actor)
        form = OperatingHoursForm(request.POST)
        if not form.is_valid():
            messages.error(request, 'Zadejte platný čas otevření a pozdější čas zavření.')
            return redirect(reverse('home') + '#staff-title')
        service.update_operating_hours(
            resource_id, actor, form.cleaned_data['opens_at'], form.cleaned_data['closes_at'],
        )
    except ReservationError as error:
        if error.code == 'unauthenticated':
            return redirect('login')
        return HttpResponse(_error_message(error), status={
            'forbidden': 403, 'not_found': 404, 'invalid_input': 400,
        }.get(error.code, 400))
    messages.success(request, 'Provozní doba byla uložená. Platí každý den pro nové rezervace a schvalování.')
    return redirect(reverse('home') + '#staff-title')
