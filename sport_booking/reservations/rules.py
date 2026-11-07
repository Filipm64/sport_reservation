from datetime import UTC, datetime, time, timedelta

from django.utils import timezone

from .domain import HourBlock, ReservationError, TimeInterval


class TimeRules:
    def now(self):
        return timezone.now()

    def validate_interval(self, interval, now):
        start, end = interval.start.astimezone(UTC), interval.end.astimezone(UTC)
        now = now.astimezone(UTC)
        error = None
        if start >= end:
            error = 'End must be after start.'
        elif start < now:
            error = 'Reservation cannot start in the past.'
        elif start > now + timedelta(days=30):
            error = 'Reservation cannot start more than 30 days ahead.'
        elif end - start > timedelta(hours=2):
            error = 'Reservation cannot be longer than 2 hours.'
        if error:
            raise ReservationError('invalid_interval', error)

    def validate_operating_hours(self, opens_at, closes_at):
        if opens_at >= closes_at:
            raise ReservationError('invalid_input', 'Opening time must be before closing time.')

    def is_within_operating_hours(self, interval, resource):
        zone = timezone.get_default_timezone()
        start, end = interval.start.astimezone(zone), interval.end.astimezone(zone)
        if resource.opens_at >= resource.closes_at or start.date() != end.date():
            return False
        opening = datetime.combine(start.date(), resource.opens_at, zone).astimezone(UTC)
        closing = datetime.combine(start.date(), resource.closes_at, zone).replace(fold=1).astimezone(UTC)
        return opening <= interval.start.astimezone(UTC) < interval.end.astimezone(UTC) <= closing

    def validate_resource_hours(self, interval, resource):
        if not self.is_within_operating_hours(interval, resource):
            raise ReservationError('outside_hours', 'Reservation must fit within operating hours.')

    def hourly_blocks(self, day, now, resource, confirmed_intervals):
        zone = timezone.get_default_timezone()
        start = datetime.combine(day, time.min, zone).astimezone(UTC)
        stop = datetime.combine(day + timedelta(days=1), time.min, zone).astimezone(UTC)
        day_length = stop - start
        blocks = []
        while start < stop:
            end = start + timedelta(hours=1)
            interval = TimeInterval(start, end)
            reason = ''
            try:
                self.validate_interval(interval, now)
            except ReservationError:
                reason = 'Mimo povolený čas'
            if not self.is_within_operating_hours(interval, resource):
                reason = 'Zavřeno'
            elif not resource.is_available:
                reason = 'Sportoviště nedostupné'
            elif self.has_conflict(interval, confirmed_intervals):
                reason = 'Obsazeno'
            local_start, local_end = start.astimezone(zone), end.astimezone(zone)
            label = f'{local_start:%H:%M}–{local_end:%H:%M}'
            if local_start.utcoffset() != local_end.utcoffset() or day_length != timedelta(days=1):
                label += f' (UTC{local_start:%z})'
            blocks.append(HourBlock(f'{day.isoformat()}:{len(blocks)}', start, end, label, not reason, reason))
            start = end
        return blocks

    def weekly_blocks(self, day, now, resource, confirmed_intervals):
        monday = day - timedelta(days=day.weekday())
        names = ('Po', 'Út', 'St', 'Čt', 'Pá', 'So', 'Ne')
        days = []
        row_keys = set()
        all_blocks = []
        for index in range(7):
            date = monday + timedelta(days=index)
            blocks = self.hourly_blocks(date, now, resource, confirmed_intervals)
            cells = {}
            for block in blocks:
                local = block.start.astimezone(timezone.get_default_timezone())
                key = (local.hour, local.fold)
                cells[key] = block
                row_keys.add(key)
            all_blocks.extend(blocks)
            days.append({'date': date, 'name': names[index], 'cells': cells})
        rows = []
        for key in sorted(row_keys):
            cells = [item['cells'].get(key) for item in days]
            # Closed hours add no useful selectable rows; partial/DST gaps remain explicit.
            if any(cell and cell.reason != 'Zavřeno' for cell in cells):
                rows.append({'label': f'{key[0]:02}:00' + (' ↺' if key[1] else ''),
                             'cells': cells})
        return {'days': days, 'rows': rows, 'blocks': all_blocks,
                'start': monday, 'end': monday + timedelta(days=6),
                'opens_at': resource.opens_at.strftime('%H:%M'),
                'closes_at': resource.closes_at.strftime('%H:%M')}

    def is_expired(self, reservation, now):
        return reservation.is_pending() and (
            reservation.approval_request is None
            or now >= reservation.approval_request.deadline(reservation.interval)
        )

    def display_status(self, reservation_listing, now):
        if reservation_listing.status == 'PENDING_APPROVAL' and now >= reservation_listing.starts_at:
            return 'EXPIRED'
        return reservation_listing.status

    def validate_approval(self, reservation, now):
        self.validate_interval(reservation.interval, now)

    def has_conflict(self, interval, confirmed_intervals):
        return any(interval.overlaps(existing) for existing in confirmed_intervals)

    def validate_cancellation(self, reservation, now):
        if now >= reservation.interval.start:
            raise ReservationError('conflict', 'Reservation has already started.')
