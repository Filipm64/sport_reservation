# Vazby požadavků, implementace a testů

Generováno z [traceability.json](traceability.json) příkazem `python3 scripts/update_docs.py`. Tento soubor neupravujte ručně.

Vazba na test označuje související ověření, nikoli výsledek jeho posledního běhu. Mapování vychází ze stávající dokumentace a symbolů v kódu; kontrola platnosti požadavků podle zadání je samostatný další krok.

[Požadavky](../requirements/README.md) · [Ověřování](README.md) · [Zpětné vazby z kódu a testů](#zpětné-vazby-z-kódu-a-testů)

## REQ-01

[Vytvoření rezervace](../requirements/create-reservation.md)

**Pravidla:** [BR-01](../requirements/business-rules.md#br-01), [BR-02](../requirements/business-rules.md#br-02), [BR-03](../requirements/business-rules.md#br-03), [BR-04](../requirements/business-rules.md#br-04), [BR-06](../requirements/business-rules.md#br-06), [BR-07](../requirements/business-rules.md#br-07), [BR-08](../requirements/business-rules.md#br-08), [BR-09](../requirements/business-rules.md#br-09)

**Návrh:** [domain-model](../design/domain-model.md)

### Implementace

- [`ReservationService.create`](../../sport_booking/reservations/services.py#L13)
- [`TimeRules.validate_interval`](../../sport_booking/reservations/rules.py#L12)

### Testy

- [`ReservationApiTests.test_create_succeeds_and_rejects_invalid_interval`](../../sport_booking/reservations/tests.py#L146)
- [`ReservationApiTests.test_exact_time_limits_and_exceeded_limits`](../../sport_booking/reservations/tests.py#L238)
- [`ReservationApiTests.test_authentication_ownership_and_unknown_resource`](../../sport_booking/reservations/tests.py#L221)
- [`ReservationApiTests.test_invalid_calendar_date_returns_error_without_creating`](../../sport_booking/reservations/tests.py#L233)
- [`ReservationApiTests.test_create_pending_checks_conflicts_and_inactive_resource`](../../sport_booking/reservations/tests.py#L155)

## REQ-02

[Kontrola dostupnosti](../requirements/check-availability.md)

**Pravidla:** [BR-01](../requirements/business-rules.md#br-01), [BR-02](../requirements/business-rules.md#br-02), [BR-03](../requirements/business-rules.md#br-03), [BR-04](../requirements/business-rules.md#br-04), [BR-07](../requirements/business-rules.md#br-07), [BR-09](../requirements/business-rules.md#br-09)

**Návrh:** [static-structure](../architecture/static-structure.md)

### Implementace

- [`AvailabilityQueries.check`](../../sport_booking/reservations/services.py#L108)
- [`TimeRules.has_conflict`](../../sport_booking/reservations/rules.py#L115)

### Testy

- [`ReservationApiTests.test_availability_checks_confirmed_only_and_half_open_edges`](../../sport_booking/reservations/tests.py#L169)
- [`ReservationApiTests.test_approval_request_does_not_block_until_staff_approves`](../../sport_booking/reservations/tests.py#L180)
- [`ReservationApiTests.test_inactive_resource_and_invalid_availability`](../../sport_booking/reservations/tests.py#L252)

## REQ-03

[Automatické potvrzení při vytvoření](../requirements/confirm-reservation.md)

**Pravidla:** [BR-01](../requirements/business-rules.md#br-01), [BR-02](../requirements/business-rules.md#br-02), [BR-03](../requirements/business-rules.md#br-03), [BR-04](../requirements/business-rules.md#br-04), [BR-06](../requirements/business-rules.md#br-06), [BR-08](../requirements/business-rules.md#br-08), [BR-09](../requirements/business-rules.md#br-09)

**Návrh:** [reservation-lifecycle](../design/reservation-lifecycle.md) · [design-classes](../design/design-classes.md)

### Implementace

- [`ReservationService.create`](../../sport_booking/reservations/services.py#L13)
- [`ReservationService._decide_confirmation`](../../sport_booking/reservations/services.py#L35)
- [`ReservationService._reject_competing_requests`](../../sport_booking/reservations/services.py#L29)

### Testy

- [`ReservationApiTests.test_create_succeeds_and_rejects_invalid_interval`](../../sport_booking/reservations/tests.py#L146)
- [`ReservationApiTests.test_create_pending_checks_conflicts_and_inactive_resource`](../../sport_booking/reservations/tests.py#L155)
- [`ReservationApiTests.test_automatic_creation_rejects_existing_pending_requests`](../../sport_booking/reservations/tests.py#L206)
- [`ReservationApiTests.test_confirm_endpoint_removed_and_terminal_states_cannot_reopen`](../../sport_booking/reservations/tests.py#L337)

## REQ-04

[Zabránění dvojí rezervaci](../requirements/prevent-double-booking.md)

**Pravidla:** [BR-02](../requirements/business-rules.md#br-02), [BR-06](../requirements/business-rules.md#br-06), [BR-08](../requirements/business-rules.md#br-08)

**Návrh:** [ADR-001-reservation-coordination](../architecture/decisions/ADR-001-reservation-coordination.md) · [approval-sequence](../design/approval-sequence.md)

### Implementace

- [`ReservationService._decide_confirmation`](../../sport_booking/reservations/services.py#L35)
- [`DjangoDataStore`](../../sport_booking/reservations/persistence.py#L32)

### Testy

- [`ReservationConcurrencyTests.test_conflicting_creations_commit_only_one_allocation`](../../sport_booking/reservations/test_concurrency.py#L62)
- [`ReservationConcurrencyTests.test_conflicting_approvals_commit_only_one_allocation`](../../sport_booking/reservations/test_concurrency.py#L71)
- [`ReservationConcurrencyTests.test_create_racing_approval_commits_only_one_allocation`](../../sport_booking/reservations/test_concurrency.py#L81)
- [`PersistenceFailureTests.test_failed_competitor_rejection_rolls_back_winner_and_losers`](../../sport_booking/reservations/test_architecture.py#L133)
- [`PersistenceFailureTests.test_failed_automatic_rejection_rolls_back_created_reservation`](../../sport_booking/reservations/test_architecture.py#L152)

## REQ-05

[Zrušení rezervace](../requirements/cancel-reservation.md)

**Pravidla:** [BR-02](../requirements/business-rules.md#br-02), [BR-05](../requirements/business-rules.md#br-05), [BR-06](../requirements/business-rules.md#br-06), [BR-07](../requirements/business-rules.md#br-07)

**Návrh:** [reservation-lifecycle](../design/reservation-lifecycle.md)

### Implementace

- [`ReservationService.cancel`](../../sport_booking/reservations/services.py#L77)
- [`TimeRules.validate_cancellation`](../../sport_booking/reservations/rules.py#L118)

### Testy

- [`ReservationApiTests.test_cancel_confirmed_releases_resource_and_rejects_repeat`](../../sport_booking/reservations/tests.py#L262)
- [`ReservationApiTests.test_owner_can_cancel_pending_approval_but_not_after_start`](../../sport_booking/reservations/tests.py#L268)
- [`ReservationApiTests.test_expiry_exact_deadline_on_approve_cancel_and_command`](../../sport_booking/reservations/tests.py#L304)
- [`ReservationApiTests.test_pending_request_remains_actionable_after_24_hours_until_start`](../../sport_booking/reservations/tests.py#L286)
- [`ReservationConcurrencyTests.test_approve_racing_cancel_finishes_cancelled`](../../sport_booking/reservations/test_concurrency.py#L93)

## REQ-06

[Schválení rezervace](../requirements/approve-reservation.md)

**Pravidla:** [BR-01](../requirements/business-rules.md#br-01), [BR-02](../requirements/business-rules.md#br-02), [BR-03](../requirements/business-rules.md#br-03), [BR-04](../requirements/business-rules.md#br-04), [BR-06](../requirements/business-rules.md#br-06), [BR-07](../requirements/business-rules.md#br-07), [BR-08](../requirements/business-rules.md#br-08), [BR-09](../requirements/business-rules.md#br-09)

**Návrh:** [approval-sequence](../design/approval-sequence.md) · [reservation-lifecycle](../design/reservation-lifecycle.md) · [detailed-design](../design/detailed-design.md)

### Implementace

- [`ReservationService.approve`](../../sport_booking/reservations/services.py#L56)
- [`ReservationService._expire_if_due`](../../sport_booking/reservations/services.py#L48)
- [`ReservationService.expire_due`](../../sport_booking/reservations/services.py#L89)
- [`IdentityAccess.require_approver`](../../sport_booking/reservations/identity.py#L22)
- [`ReservationService._reject_competing_requests`](../../sport_booking/reservations/services.py#L29)
- [`DjangoDataStore.overlapping_pending_ids`](../../sport_booking/reservations/persistence.py#L95)

### Testy

- [`ReservationApiTests.test_delayed_approval_succeeds_after_24_hours_before_start`](../../sport_booking/reservations/tests.py#L279)
- [`ReservationApiTests.test_staff_can_reject_but_non_staff_cannot_decide`](../../sport_booking/reservations/tests.py#L215)
- [`ReservationApiTests.test_expiry_exact_deadline_on_approve_cancel_and_command`](../../sport_booking/reservations/tests.py#L304)
- [`ReservationApiTests.test_pending_request_remains_actionable_after_24_hours_until_start`](../../sport_booking/reservations/tests.py#L286)
- [`ReservationApiTests.test_confirmation_rejects_only_overlapping_pending_same_resource`](../../sport_booking/reservations/tests.py#L191)
- [`ReservationApiTests.test_invalid_approval_decision_is_rejected_without_state_change`](../../sport_booking/reservations/tests.py#L330)

## REQ-07

[Veřejný katalog sportovišť](../requirements/public-catalog.md)

**Pravidla:** Podmínky a oprávnění jsou uvedené přímo u požadavku.

**Návrh:** [web-portal](../design/web-portal.md)

### Implementace

- [`home`](../../sport_booking/reservations/web_views.py#L138)
- [`PortalQueries.resources`](../../sport_booking/reservations/portal.py#L12)
- [`DjangoDataStore.list_resources`](../../sport_booking/reservations/persistence.py#L109)

### Testy

- [`PortalRequirementTests.test_public_catalog_shows_metadata_and_operating_availability`](../../sport_booking/reservations/test_portal_requirements.py#L40)
- [`PortalRequirementTests.test_empty_public_catalog_is_displayed_without_error`](../../sport_booking/reservations/test_portal_requirements.py#L51)
- [`PortalRequirementTests.test_guest_and_customer_cannot_see_staff_queue`](../../sport_booking/reservations/test_portal_requirements.py#L176)

## REQ-08

[Registrace zákazníka](../requirements/customer-registration.md)

**Pravidla:** Podmínky a oprávnění jsou uvedené přímo u požadavku.

**Návrh:** [web-portal](../design/web-portal.md)

### Implementace

- [`RegistrationForm`](../../sport_booking/reservations/web_views.py#L21)
- [`register`](../../sport_booking/reservations/web_views.py#L278)

### Testy

- [`PortalRequirementTests.test_registration_creates_only_customer_and_authenticates`](../../sport_booking/reservations/test_portal_requirements.py#L58)
- [`PortalRequirementTests.test_invalid_registration_does_not_create_or_authenticate_user`](../../sport_booking/reservations/test_portal_requirements.py#L75)
- [`PortalRequirementTests.test_authenticated_user_cannot_create_second_account`](../../sport_booking/reservations/test_portal_requirements.py#L92)
- [`PortalRequirementTests.test_account_forms_require_csrf`](../../sport_booking/reservations/test_portal_requirements.py#L141)
- [`PortalRequirementTests.test_account_forms_work_with_valid_csrf_tokens`](../../sport_booking/reservations/test_portal_requirements.py#L237)

## REQ-09

[Přihlášení a odhlášení](../requirements/login-logout.md)

**Pravidla:** Podmínky a oprávnění jsou uvedené přímo u požadavku.

**Návrh:** [web-portal](../design/web-portal.md)

### Implementace

- [`PortalLoginView`](../../sport_booking/reservations/web_views.py#L290)
- [`PortalLogoutView`](../../sport_booking/reservations/web_views.py#L295)

### Testy

- [`PortalRequirementTests.test_login_accepts_active_customer_and_staff`](../../sport_booking/reservations/test_portal_requirements.py#L102)
- [`PortalRequirementTests.test_login_rejects_invalid_credentials_and_inactive_account`](../../sport_booking/reservations/test_portal_requirements.py#L112)
- [`PortalRequirementTests.test_login_does_not_redirect_to_untrusted_host`](../../sport_booking/reservations/test_portal_requirements.py#L126)
- [`PortalRequirementTests.test_logout_requires_post_and_ends_session`](../../sport_booking/reservations/test_portal_requirements.py#L132)
- [`PortalRequirementTests.test_account_forms_require_csrf`](../../sport_booking/reservations/test_portal_requirements.py#L141)
- [`PortalRequirementTests.test_account_forms_work_with_valid_csrf_tokens`](../../sport_booking/reservations/test_portal_requirements.py#L237)

## REQ-10

[Zobrazení vlastních rezervací](../requirements/my-reservations.md)

**Pravidla:** [BR-05](../requirements/business-rules.md#br-05), [BR-07](../requirements/business-rules.md#br-07)

**Návrh:** [web-portal](../design/web-portal.md)

### Implementace

- [`home`](../../sport_booking/reservations/web_views.py#L138)
- [`PortalQueries.reservations_for_user`](../../sport_booking/reservations/portal.py#L16)
- [`DjangoDataStore.list_reservations`](../../sport_booking/reservations/persistence.py#L119)
- [`DjangoDataStore._reservation_listings`](../../sport_booking/reservations/persistence.py#L131)
- [`TimeRules.display_status`](../../sport_booking/reservations/rules.py#L107)

### Testy

- [`PortalRequirementTests.test_customer_sees_only_own_reservations_in_all_five_states`](../../sport_booking/reservations/test_portal_requirements.py#L151)
- [`PortalRequirementTests.test_staff_personal_list_still_contains_only_own_reservations`](../../sport_booking/reservations/test_portal_requirements.py#L169)
- [`PortalRequirementTests.test_customer_with_no_reservations_sees_empty_state`](../../sport_booking/reservations/test_portal_requirements.py#L189)
- [`PortalRequirementTests.test_guest_and_customer_cannot_see_staff_queue`](../../sport_booking/reservations/test_portal_requirements.py#L176)
- [`PortalRequirementTests.test_personal_list_displays_effective_expiry_without_writing_database`](../../sport_booking/reservations/test_portal_requirements.py#L225)

## REQ-11

[Přehled čekajících žádostí správce](../requirements/staff-approval-queue.md)

**Pravidla:** [BR-07](../requirements/business-rules.md#br-07)

**Návrh:** [web-portal](../design/web-portal.md)

### Implementace

- [`home`](../../sport_booking/reservations/web_views.py#L138)
- [`PortalQueries.pending_reservations`](../../sport_booking/reservations/portal.py#L22)
- [`DjangoDataStore.list_pending_reservations`](../../sport_booking/reservations/persistence.py#L123)

### Testy

- [`PortalRequirementTests.test_guest_and_customer_cannot_see_staff_queue`](../../sport_booking/reservations/test_portal_requirements.py#L176)
- [`PortalRequirementTests.test_staff_queue_shows_only_pending_before_start_without_mutation`](../../sport_booking/reservations/test_portal_requirements.py#L196)
- [`PortalRequirementTests.test_staff_queue_displays_empty_state`](../../sport_booking/reservations/test_portal_requirements.py#L219)
- [`PortalTests.test_non_staff_cannot_approve_pending_reservation`](../../sport_booking/reservations/test_portal.py#L103)

## REQ-12

[Výběr rezervace z hodinového rozvrhu](../requirements/hourly-schedule.md)

**Pravidla:** [BR-01](../requirements/business-rules.md#br-01), [BR-02](../requirements/business-rules.md#br-02), [BR-03](../requirements/business-rules.md#br-03), [BR-04](../requirements/business-rules.md#br-04), [BR-07](../requirements/business-rules.md#br-07), [BR-09](../requirements/business-rules.md#br-09)

**Návrh:** [hourly-schedule](../design/hourly-schedule.md)

### Implementace

- [`ScheduleFilterForm`](../../sport_booking/reservations/web_views.py#L41)
- [`BookingForm.clean`](../../sport_booking/reservations/web_views.py#L115)
- [`home`](../../sport_booking/reservations/web_views.py#L138)
- [`PortalQueries.weekly_schedule`](../../sport_booking/reservations/portal.py#L32)
- [`TimeRules.weekly_blocks`](../../sport_booking/reservations/rules.py#L72)
- [`TimeRules.validate_interval`](../../sport_booking/reservations/rules.py#L12)
- [`ReservationService.create`](../../sport_booking/reservations/services.py#L13)
- [`home.html`](../../sport_booking/reservations/templates/reservations/home.html)
- [`schedule.js`](../../sport_booking/reservations/static/reservations/schedule.js)
- [`app.css`](../../sport_booking/reservations/static/reservations/app.css)

### Testy

- [`ScheduleTests.test_grid_renders_hour_blocks_and_manual_option`](../../sport_booking/reservations/test_schedule.py#L86)
- [`ScheduleTests.test_one_or_two_blocks_create_exact_one_or_two_hour_reservation`](../../sport_booking/reservations/test_schedule.py#L95)
- [`ScheduleTests.test_three_nonadjacent_duplicate_and_unknown_blocks_are_rejected`](../../sport_booking/reservations/test_schedule.py#L107)
- [`ScheduleTests.test_confirmed_partial_overlap_blocks_whole_hour_and_edges_remain_free`](../../sport_booking/reservations/test_schedule.py#L115)
- [`ScheduleTests.test_pending_other_resource_and_cancelled_do_not_block`](../../sport_booking/reservations/test_schedule.py#L131)
- [`ScheduleTests.test_approval_required_resource_creates_pending_from_blocks`](../../sport_booking/reservations/test_schedule.py#L142)
- [`ScheduleTests.test_stale_schedule_does_not_bypass_atomic_conflict_check`](../../sport_booking/reservations/test_schedule.py#L150)
- [`ScheduleTests.test_invalid_resource_and_day_do_not_create_reservation`](../../sport_booking/reservations/test_schedule.py#L161)
- [`ScheduleTests.test_past_and_beyond_thirty_days_are_disabled`](../../sport_booking/reservations/test_schedule.py#L170)
- [`ScheduleTests.test_availability_from_blocks_is_read_only`](../../sport_booking/reservations/test_schedule.py#L178)
- [`ScheduleTests.test_manual_input_keeps_two_hour_server_limit`](../../sport_booking/reservations/test_schedule.py#L182)
- [`ScheduleTests.test_guest_cannot_submit_grid_booking`](../../sport_booking/reservations/test_schedule.py#L193)
- [`ScheduleTests.test_slot_interval_is_derived_on_server_not_client_values`](../../sport_booking/reservations/test_schedule.py#L198)
- [`HourBlockRuleTests.test_daylight_saving_days_have_real_hour_blocks`](../../sport_booking/reservations/test_schedule.py#L16)
- [`HourBlockRuleTests.test_two_hour_limit_uses_elapsed_time_across_dst`](../../sport_booking/reservations/test_schedule.py#L29)
- [`HourBlockRuleTests.test_unavailable_resource_disables_all_blocks`](../../sport_booking/reservations/test_schedule.py#L42)
- [`OperatingHoursTests.test_week_grid_excludes_closed_rows_and_disables_partial_hours`](../../sport_booking/reservations/test_operating_hours.py#L77)
- [`OperatingHoursTests.test_week_navigation_stays_inside_booking_horizon`](../../sport_booking/reservations/test_operating_hours.py#L94)
- [`OperatingHoursTests.test_week_selection_is_limited_to_one_day`](../../sport_booking/reservations/test_operating_hours.py#L103)
- [`OperatingHoursTests.test_block_from_other_day_in_same_week_creates_correct_date`](../../sport_booking/reservations/test_operating_hours.py#L116)
- [`HourBlockRuleTests.test_week_table_represents_dst_gap_and_repeated_hour`](../../sport_booking/reservations/test_schedule.py#L49)

## REQ-13

[Nastavení a vynucování provozní doby](../requirements/operating-hours.md)

**Pravidla:** [BR-01](../requirements/business-rules.md#br-01), [BR-03](../requirements/business-rules.md#br-03), [BR-04](../requirements/business-rules.md#br-04), [BR-09](../requirements/business-rules.md#br-09)

**Návrh:** [hourly-schedule](../design/hourly-schedule.md)

### Implementace

- [`OperatingHoursForm`](../../sport_booking/reservations/web_views.py#L27)
- [`update_operating_hours`](../../sport_booking/reservations/web_views.py#L317)
- [`ResourceService.update_operating_hours`](../../sport_booking/reservations/services.py#L125)
- [`ReservationService._decide_confirmation`](../../sport_booking/reservations/services.py#L35)
- [`AvailabilityQueries.check`](../../sport_booking/reservations/services.py#L108)
- [`TimeRules.validate_operating_hours`](../../sport_booking/reservations/rules.py#L27)
- [`TimeRules.is_within_operating_hours`](../../sport_booking/reservations/rules.py#L31)
- [`DjangoDataStore.set_operating_hours`](../../sport_booking/reservations/persistence.py#L71)
- [`Resource.clean`](../../sport_booking/reservations/models.py#L22)

### Testy

- [`OperatingHoursTests.test_api_creation_rejects_outside_hours_for_both_resource_types`](../../sport_booking/reservations/test_operating_hours.py#L43)
- [`OperatingHoursTests.test_exact_opening_and_closing_boundaries_are_allowed`](../../sport_booking/reservations/test_operating_hours.py#L54)
- [`OperatingHoursTests.test_availability_is_unavailable_outside_operating_hours`](../../sport_booking/reservations/test_operating_hours.py#L59)
- [`OperatingHoursTests.test_manual_web_creation_cannot_bypass_operating_hours`](../../sport_booking/reservations/test_operating_hours.py#L68)
- [`OperatingHoursTests.test_week_grid_excludes_closed_rows_and_disables_partial_hours`](../../sport_booking/reservations/test_operating_hours.py#L77)
- [`OperatingHoursTests.test_week_navigation_stays_inside_booking_horizon`](../../sport_booking/reservations/test_operating_hours.py#L94)
- [`OperatingHoursTests.test_week_selection_is_limited_to_one_day`](../../sport_booking/reservations/test_operating_hours.py#L103)
- [`OperatingHoursTests.test_block_from_other_day_in_same_week_creates_correct_date`](../../sport_booking/reservations/test_operating_hours.py#L116)
- [`OperatingHoursTests.test_staff_can_update_operating_hours_without_admin_model_permissions`](../../sport_booking/reservations/test_operating_hours.py#L131)
- [`OperatingHoursTests.test_customer_and_guest_cannot_update_operating_hours`](../../sport_booking/reservations/test_operating_hours.py#L140)
- [`OperatingHoursTests.test_invalid_operating_hours_do_not_change_configuration`](../../sport_booking/reservations/test_operating_hours.py#L148)
- [`OperatingHoursTests.test_operating_hours_update_requires_post_and_csrf`](../../sport_booking/reservations/test_operating_hours.py#L160)
- [`OperatingHoursTests.test_approval_rechecks_changed_operating_hours`](../../sport_booking/reservations/test_operating_hours.py#L173)
- [`OperatingHoursTests.test_changing_operating_hours_does_not_cancel_existing_confirmations`](../../sport_booking/reservations/test_operating_hours.py#L184)
- [`OperatingHoursTests.test_api_uses_local_operating_time_regardless_of_input_offset`](../../sport_booking/reservations/test_operating_hours.py#L190)
- [`OperatingHoursTests.test_operating_hours_update_rolls_back_when_commit_fails`](../../sport_booking/reservations/test_operating_hours.py#L197)
- [`OperatingHoursTests.test_partial_hour_manual_interval_can_fit_and_overnight_is_rejected`](../../sport_booking/reservations/test_operating_hours.py#L207)

## Zpětné vazby z kódu a testů

Vyhledejte název metody nebo testu a otevřete související požadavek.

| Soubor | Symbol | Požadavky |
| --- | --- | --- |
| [identity.py](../../sport_booking/reservations/identity.py) | [`IdentityAccess.require_approver`](../../sport_booking/reservations/identity.py#L22) | [REQ-06](../requirements/approve-reservation.md) |
| [models.py](../../sport_booking/reservations/models.py) | [`Resource.clean`](../../sport_booking/reservations/models.py#L22) | [REQ-13](../requirements/operating-hours.md) |
| [persistence.py](../../sport_booking/reservations/persistence.py) | [`DjangoDataStore`](../../sport_booking/reservations/persistence.py#L32) | [REQ-04](../requirements/prevent-double-booking.md) |
| [persistence.py](../../sport_booking/reservations/persistence.py) | [`DjangoDataStore._reservation_listings`](../../sport_booking/reservations/persistence.py#L131) | [REQ-10](../requirements/my-reservations.md) |
| [persistence.py](../../sport_booking/reservations/persistence.py) | [`DjangoDataStore.list_pending_reservations`](../../sport_booking/reservations/persistence.py#L123) | [REQ-11](../requirements/staff-approval-queue.md) |
| [persistence.py](../../sport_booking/reservations/persistence.py) | [`DjangoDataStore.list_reservations`](../../sport_booking/reservations/persistence.py#L119) | [REQ-10](../requirements/my-reservations.md) |
| [persistence.py](../../sport_booking/reservations/persistence.py) | [`DjangoDataStore.list_resources`](../../sport_booking/reservations/persistence.py#L109) | [REQ-07](../requirements/public-catalog.md) |
| [persistence.py](../../sport_booking/reservations/persistence.py) | [`DjangoDataStore.overlapping_pending_ids`](../../sport_booking/reservations/persistence.py#L95) | [REQ-06](../requirements/approve-reservation.md) |
| [persistence.py](../../sport_booking/reservations/persistence.py) | [`DjangoDataStore.set_operating_hours`](../../sport_booking/reservations/persistence.py#L71) | [REQ-13](../requirements/operating-hours.md) |
| [portal.py](../../sport_booking/reservations/portal.py) | [`PortalQueries.pending_reservations`](../../sport_booking/reservations/portal.py#L22) | [REQ-11](../requirements/staff-approval-queue.md) |
| [portal.py](../../sport_booking/reservations/portal.py) | [`PortalQueries.reservations_for_user`](../../sport_booking/reservations/portal.py#L16) | [REQ-10](../requirements/my-reservations.md) |
| [portal.py](../../sport_booking/reservations/portal.py) | [`PortalQueries.resources`](../../sport_booking/reservations/portal.py#L12) | [REQ-07](../requirements/public-catalog.md) |
| [portal.py](../../sport_booking/reservations/portal.py) | [`PortalQueries.weekly_schedule`](../../sport_booking/reservations/portal.py#L32) | [REQ-12](../requirements/hourly-schedule.md) |
| [rules.py](../../sport_booking/reservations/rules.py) | [`TimeRules.display_status`](../../sport_booking/reservations/rules.py#L107) | [REQ-10](../requirements/my-reservations.md) |
| [rules.py](../../sport_booking/reservations/rules.py) | [`TimeRules.has_conflict`](../../sport_booking/reservations/rules.py#L115) | [REQ-02](../requirements/check-availability.md) |
| [rules.py](../../sport_booking/reservations/rules.py) | [`TimeRules.is_within_operating_hours`](../../sport_booking/reservations/rules.py#L31) | [REQ-13](../requirements/operating-hours.md) |
| [rules.py](../../sport_booking/reservations/rules.py) | [`TimeRules.validate_cancellation`](../../sport_booking/reservations/rules.py#L118) | [REQ-05](../requirements/cancel-reservation.md) |
| [rules.py](../../sport_booking/reservations/rules.py) | [`TimeRules.validate_interval`](../../sport_booking/reservations/rules.py#L12) | [REQ-01](../requirements/create-reservation.md), [REQ-12](../requirements/hourly-schedule.md) |
| [rules.py](../../sport_booking/reservations/rules.py) | [`TimeRules.validate_operating_hours`](../../sport_booking/reservations/rules.py#L27) | [REQ-13](../requirements/operating-hours.md) |
| [rules.py](../../sport_booking/reservations/rules.py) | [`TimeRules.weekly_blocks`](../../sport_booking/reservations/rules.py#L72) | [REQ-12](../requirements/hourly-schedule.md) |
| [services.py](../../sport_booking/reservations/services.py) | [`AvailabilityQueries.check`](../../sport_booking/reservations/services.py#L108) | [REQ-02](../requirements/check-availability.md), [REQ-13](../requirements/operating-hours.md) |
| [services.py](../../sport_booking/reservations/services.py) | [`ReservationService._decide_confirmation`](../../sport_booking/reservations/services.py#L35) | [REQ-03](../requirements/confirm-reservation.md), [REQ-04](../requirements/prevent-double-booking.md), [REQ-13](../requirements/operating-hours.md) |
| [services.py](../../sport_booking/reservations/services.py) | [`ReservationService._expire_if_due`](../../sport_booking/reservations/services.py#L48) | [REQ-06](../requirements/approve-reservation.md) |
| [services.py](../../sport_booking/reservations/services.py) | [`ReservationService._reject_competing_requests`](../../sport_booking/reservations/services.py#L29) | [REQ-03](../requirements/confirm-reservation.md), [REQ-06](../requirements/approve-reservation.md) |
| [services.py](../../sport_booking/reservations/services.py) | [`ReservationService.approve`](../../sport_booking/reservations/services.py#L56) | [REQ-06](../requirements/approve-reservation.md) |
| [services.py](../../sport_booking/reservations/services.py) | [`ReservationService.cancel`](../../sport_booking/reservations/services.py#L77) | [REQ-05](../requirements/cancel-reservation.md) |
| [services.py](../../sport_booking/reservations/services.py) | [`ReservationService.create`](../../sport_booking/reservations/services.py#L13) | [REQ-01](../requirements/create-reservation.md), [REQ-03](../requirements/confirm-reservation.md), [REQ-12](../requirements/hourly-schedule.md) |
| [services.py](../../sport_booking/reservations/services.py) | [`ReservationService.expire_due`](../../sport_booking/reservations/services.py#L89) | [REQ-06](../requirements/approve-reservation.md) |
| [services.py](../../sport_booking/reservations/services.py) | [`ResourceService.update_operating_hours`](../../sport_booking/reservations/services.py#L125) | [REQ-13](../requirements/operating-hours.md) |
| [app.css](../../sport_booking/reservations/static/reservations/app.css) | [`app.css`](../../sport_booking/reservations/static/reservations/app.css) | [REQ-12](../requirements/hourly-schedule.md) |
| [schedule.js](../../sport_booking/reservations/static/reservations/schedule.js) | [`schedule.js`](../../sport_booking/reservations/static/reservations/schedule.js) | [REQ-12](../requirements/hourly-schedule.md) |
| [home.html](../../sport_booking/reservations/templates/reservations/home.html) | [`home.html`](../../sport_booking/reservations/templates/reservations/home.html) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_architecture.py](../../sport_booking/reservations/test_architecture.py) | [`PersistenceFailureTests.test_failed_automatic_rejection_rolls_back_created_reservation`](../../sport_booking/reservations/test_architecture.py#L152) | [REQ-04](../requirements/prevent-double-booking.md) |
| [test_architecture.py](../../sport_booking/reservations/test_architecture.py) | [`PersistenceFailureTests.test_failed_competitor_rejection_rolls_back_winner_and_losers`](../../sport_booking/reservations/test_architecture.py#L133) | [REQ-04](../requirements/prevent-double-booking.md) |
| [test_concurrency.py](../../sport_booking/reservations/test_concurrency.py) | [`ReservationConcurrencyTests.test_approve_racing_cancel_finishes_cancelled`](../../sport_booking/reservations/test_concurrency.py#L93) | [REQ-05](../requirements/cancel-reservation.md) |
| [test_concurrency.py](../../sport_booking/reservations/test_concurrency.py) | [`ReservationConcurrencyTests.test_conflicting_approvals_commit_only_one_allocation`](../../sport_booking/reservations/test_concurrency.py#L71) | [REQ-04](../requirements/prevent-double-booking.md) |
| [test_concurrency.py](../../sport_booking/reservations/test_concurrency.py) | [`ReservationConcurrencyTests.test_conflicting_creations_commit_only_one_allocation`](../../sport_booking/reservations/test_concurrency.py#L62) | [REQ-04](../requirements/prevent-double-booking.md) |
| [test_concurrency.py](../../sport_booking/reservations/test_concurrency.py) | [`ReservationConcurrencyTests.test_create_racing_approval_commits_only_one_allocation`](../../sport_booking/reservations/test_concurrency.py#L81) | [REQ-04](../requirements/prevent-double-booking.md) |
| [test_operating_hours.py](../../sport_booking/reservations/test_operating_hours.py) | [`OperatingHoursTests.test_api_creation_rejects_outside_hours_for_both_resource_types`](../../sport_booking/reservations/test_operating_hours.py#L43) | [REQ-13](../requirements/operating-hours.md) |
| [test_operating_hours.py](../../sport_booking/reservations/test_operating_hours.py) | [`OperatingHoursTests.test_api_uses_local_operating_time_regardless_of_input_offset`](../../sport_booking/reservations/test_operating_hours.py#L190) | [REQ-13](../requirements/operating-hours.md) |
| [test_operating_hours.py](../../sport_booking/reservations/test_operating_hours.py) | [`OperatingHoursTests.test_approval_rechecks_changed_operating_hours`](../../sport_booking/reservations/test_operating_hours.py#L173) | [REQ-13](../requirements/operating-hours.md) |
| [test_operating_hours.py](../../sport_booking/reservations/test_operating_hours.py) | [`OperatingHoursTests.test_availability_is_unavailable_outside_operating_hours`](../../sport_booking/reservations/test_operating_hours.py#L59) | [REQ-13](../requirements/operating-hours.md) |
| [test_operating_hours.py](../../sport_booking/reservations/test_operating_hours.py) | [`OperatingHoursTests.test_block_from_other_day_in_same_week_creates_correct_date`](../../sport_booking/reservations/test_operating_hours.py#L116) | [REQ-12](../requirements/hourly-schedule.md), [REQ-13](../requirements/operating-hours.md) |
| [test_operating_hours.py](../../sport_booking/reservations/test_operating_hours.py) | [`OperatingHoursTests.test_changing_operating_hours_does_not_cancel_existing_confirmations`](../../sport_booking/reservations/test_operating_hours.py#L184) | [REQ-13](../requirements/operating-hours.md) |
| [test_operating_hours.py](../../sport_booking/reservations/test_operating_hours.py) | [`OperatingHoursTests.test_customer_and_guest_cannot_update_operating_hours`](../../sport_booking/reservations/test_operating_hours.py#L140) | [REQ-13](../requirements/operating-hours.md) |
| [test_operating_hours.py](../../sport_booking/reservations/test_operating_hours.py) | [`OperatingHoursTests.test_exact_opening_and_closing_boundaries_are_allowed`](../../sport_booking/reservations/test_operating_hours.py#L54) | [REQ-13](../requirements/operating-hours.md) |
| [test_operating_hours.py](../../sport_booking/reservations/test_operating_hours.py) | [`OperatingHoursTests.test_invalid_operating_hours_do_not_change_configuration`](../../sport_booking/reservations/test_operating_hours.py#L148) | [REQ-13](../requirements/operating-hours.md) |
| [test_operating_hours.py](../../sport_booking/reservations/test_operating_hours.py) | [`OperatingHoursTests.test_manual_web_creation_cannot_bypass_operating_hours`](../../sport_booking/reservations/test_operating_hours.py#L68) | [REQ-13](../requirements/operating-hours.md) |
| [test_operating_hours.py](../../sport_booking/reservations/test_operating_hours.py) | [`OperatingHoursTests.test_operating_hours_update_requires_post_and_csrf`](../../sport_booking/reservations/test_operating_hours.py#L160) | [REQ-13](../requirements/operating-hours.md) |
| [test_operating_hours.py](../../sport_booking/reservations/test_operating_hours.py) | [`OperatingHoursTests.test_operating_hours_update_rolls_back_when_commit_fails`](../../sport_booking/reservations/test_operating_hours.py#L197) | [REQ-13](../requirements/operating-hours.md) |
| [test_operating_hours.py](../../sport_booking/reservations/test_operating_hours.py) | [`OperatingHoursTests.test_partial_hour_manual_interval_can_fit_and_overnight_is_rejected`](../../sport_booking/reservations/test_operating_hours.py#L207) | [REQ-13](../requirements/operating-hours.md) |
| [test_operating_hours.py](../../sport_booking/reservations/test_operating_hours.py) | [`OperatingHoursTests.test_staff_can_update_operating_hours_without_admin_model_permissions`](../../sport_booking/reservations/test_operating_hours.py#L131) | [REQ-13](../requirements/operating-hours.md) |
| [test_operating_hours.py](../../sport_booking/reservations/test_operating_hours.py) | [`OperatingHoursTests.test_week_grid_excludes_closed_rows_and_disables_partial_hours`](../../sport_booking/reservations/test_operating_hours.py#L77) | [REQ-12](../requirements/hourly-schedule.md), [REQ-13](../requirements/operating-hours.md) |
| [test_operating_hours.py](../../sport_booking/reservations/test_operating_hours.py) | [`OperatingHoursTests.test_week_navigation_stays_inside_booking_horizon`](../../sport_booking/reservations/test_operating_hours.py#L94) | [REQ-12](../requirements/hourly-schedule.md), [REQ-13](../requirements/operating-hours.md) |
| [test_operating_hours.py](../../sport_booking/reservations/test_operating_hours.py) | [`OperatingHoursTests.test_week_selection_is_limited_to_one_day`](../../sport_booking/reservations/test_operating_hours.py#L103) | [REQ-12](../requirements/hourly-schedule.md), [REQ-13](../requirements/operating-hours.md) |
| [test_portal.py](../../sport_booking/reservations/test_portal.py) | [`PortalTests.test_non_staff_cannot_approve_pending_reservation`](../../sport_booking/reservations/test_portal.py#L103) | [REQ-11](../requirements/staff-approval-queue.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_account_forms_require_csrf`](../../sport_booking/reservations/test_portal_requirements.py#L141) | [REQ-08](../requirements/customer-registration.md), [REQ-09](../requirements/login-logout.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_account_forms_work_with_valid_csrf_tokens`](../../sport_booking/reservations/test_portal_requirements.py#L237) | [REQ-08](../requirements/customer-registration.md), [REQ-09](../requirements/login-logout.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_authenticated_user_cannot_create_second_account`](../../sport_booking/reservations/test_portal_requirements.py#L92) | [REQ-08](../requirements/customer-registration.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_customer_sees_only_own_reservations_in_all_five_states`](../../sport_booking/reservations/test_portal_requirements.py#L151) | [REQ-10](../requirements/my-reservations.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_customer_with_no_reservations_sees_empty_state`](../../sport_booking/reservations/test_portal_requirements.py#L189) | [REQ-10](../requirements/my-reservations.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_empty_public_catalog_is_displayed_without_error`](../../sport_booking/reservations/test_portal_requirements.py#L51) | [REQ-07](../requirements/public-catalog.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_guest_and_customer_cannot_see_staff_queue`](../../sport_booking/reservations/test_portal_requirements.py#L176) | [REQ-07](../requirements/public-catalog.md), [REQ-10](../requirements/my-reservations.md), [REQ-11](../requirements/staff-approval-queue.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_invalid_registration_does_not_create_or_authenticate_user`](../../sport_booking/reservations/test_portal_requirements.py#L75) | [REQ-08](../requirements/customer-registration.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_login_accepts_active_customer_and_staff`](../../sport_booking/reservations/test_portal_requirements.py#L102) | [REQ-09](../requirements/login-logout.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_login_does_not_redirect_to_untrusted_host`](../../sport_booking/reservations/test_portal_requirements.py#L126) | [REQ-09](../requirements/login-logout.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_login_rejects_invalid_credentials_and_inactive_account`](../../sport_booking/reservations/test_portal_requirements.py#L112) | [REQ-09](../requirements/login-logout.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_logout_requires_post_and_ends_session`](../../sport_booking/reservations/test_portal_requirements.py#L132) | [REQ-09](../requirements/login-logout.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_personal_list_displays_effective_expiry_without_writing_database`](../../sport_booking/reservations/test_portal_requirements.py#L225) | [REQ-10](../requirements/my-reservations.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_public_catalog_shows_metadata_and_operating_availability`](../../sport_booking/reservations/test_portal_requirements.py#L40) | [REQ-07](../requirements/public-catalog.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_registration_creates_only_customer_and_authenticates`](../../sport_booking/reservations/test_portal_requirements.py#L58) | [REQ-08](../requirements/customer-registration.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_staff_personal_list_still_contains_only_own_reservations`](../../sport_booking/reservations/test_portal_requirements.py#L169) | [REQ-10](../requirements/my-reservations.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_staff_queue_displays_empty_state`](../../sport_booking/reservations/test_portal_requirements.py#L219) | [REQ-11](../requirements/staff-approval-queue.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_staff_queue_shows_only_pending_before_start_without_mutation`](../../sport_booking/reservations/test_portal_requirements.py#L196) | [REQ-11](../requirements/staff-approval-queue.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`HourBlockRuleTests.test_daylight_saving_days_have_real_hour_blocks`](../../sport_booking/reservations/test_schedule.py#L16) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`HourBlockRuleTests.test_two_hour_limit_uses_elapsed_time_across_dst`](../../sport_booking/reservations/test_schedule.py#L29) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`HourBlockRuleTests.test_unavailable_resource_disables_all_blocks`](../../sport_booking/reservations/test_schedule.py#L42) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`HourBlockRuleTests.test_week_table_represents_dst_gap_and_repeated_hour`](../../sport_booking/reservations/test_schedule.py#L49) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`ScheduleTests.test_approval_required_resource_creates_pending_from_blocks`](../../sport_booking/reservations/test_schedule.py#L142) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`ScheduleTests.test_availability_from_blocks_is_read_only`](../../sport_booking/reservations/test_schedule.py#L178) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`ScheduleTests.test_confirmed_partial_overlap_blocks_whole_hour_and_edges_remain_free`](../../sport_booking/reservations/test_schedule.py#L115) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`ScheduleTests.test_grid_renders_hour_blocks_and_manual_option`](../../sport_booking/reservations/test_schedule.py#L86) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`ScheduleTests.test_guest_cannot_submit_grid_booking`](../../sport_booking/reservations/test_schedule.py#L193) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`ScheduleTests.test_invalid_resource_and_day_do_not_create_reservation`](../../sport_booking/reservations/test_schedule.py#L161) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`ScheduleTests.test_manual_input_keeps_two_hour_server_limit`](../../sport_booking/reservations/test_schedule.py#L182) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`ScheduleTests.test_one_or_two_blocks_create_exact_one_or_two_hour_reservation`](../../sport_booking/reservations/test_schedule.py#L95) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`ScheduleTests.test_past_and_beyond_thirty_days_are_disabled`](../../sport_booking/reservations/test_schedule.py#L170) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`ScheduleTests.test_pending_other_resource_and_cancelled_do_not_block`](../../sport_booking/reservations/test_schedule.py#L131) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`ScheduleTests.test_slot_interval_is_derived_on_server_not_client_values`](../../sport_booking/reservations/test_schedule.py#L198) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`ScheduleTests.test_stale_schedule_does_not_bypass_atomic_conflict_check`](../../sport_booking/reservations/test_schedule.py#L150) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`ScheduleTests.test_three_nonadjacent_duplicate_and_unknown_blocks_are_rejected`](../../sport_booking/reservations/test_schedule.py#L107) | [REQ-12](../requirements/hourly-schedule.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_approval_request_does_not_block_until_staff_approves`](../../sport_booking/reservations/tests.py#L180) | [REQ-02](../requirements/check-availability.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_authentication_ownership_and_unknown_resource`](../../sport_booking/reservations/tests.py#L221) | [REQ-01](../requirements/create-reservation.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_automatic_creation_rejects_existing_pending_requests`](../../sport_booking/reservations/tests.py#L206) | [REQ-03](../requirements/confirm-reservation.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_availability_checks_confirmed_only_and_half_open_edges`](../../sport_booking/reservations/tests.py#L169) | [REQ-02](../requirements/check-availability.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_cancel_confirmed_releases_resource_and_rejects_repeat`](../../sport_booking/reservations/tests.py#L262) | [REQ-05](../requirements/cancel-reservation.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_confirm_endpoint_removed_and_terminal_states_cannot_reopen`](../../sport_booking/reservations/tests.py#L337) | [REQ-03](../requirements/confirm-reservation.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_confirmation_rejects_only_overlapping_pending_same_resource`](../../sport_booking/reservations/tests.py#L191) | [REQ-06](../requirements/approve-reservation.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_create_pending_checks_conflicts_and_inactive_resource`](../../sport_booking/reservations/tests.py#L155) | [REQ-01](../requirements/create-reservation.md), [REQ-03](../requirements/confirm-reservation.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_create_succeeds_and_rejects_invalid_interval`](../../sport_booking/reservations/tests.py#L146) | [REQ-01](../requirements/create-reservation.md), [REQ-03](../requirements/confirm-reservation.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_delayed_approval_succeeds_after_24_hours_before_start`](../../sport_booking/reservations/tests.py#L279) | [REQ-06](../requirements/approve-reservation.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_exact_time_limits_and_exceeded_limits`](../../sport_booking/reservations/tests.py#L238) | [REQ-01](../requirements/create-reservation.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_expiry_exact_deadline_on_approve_cancel_and_command`](../../sport_booking/reservations/tests.py#L304) | [REQ-05](../requirements/cancel-reservation.md), [REQ-06](../requirements/approve-reservation.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_inactive_resource_and_invalid_availability`](../../sport_booking/reservations/tests.py#L252) | [REQ-02](../requirements/check-availability.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_invalid_approval_decision_is_rejected_without_state_change`](../../sport_booking/reservations/tests.py#L330) | [REQ-06](../requirements/approve-reservation.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_invalid_calendar_date_returns_error_without_creating`](../../sport_booking/reservations/tests.py#L233) | [REQ-01](../requirements/create-reservation.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_owner_can_cancel_pending_approval_but_not_after_start`](../../sport_booking/reservations/tests.py#L268) | [REQ-05](../requirements/cancel-reservation.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_pending_request_remains_actionable_after_24_hours_until_start`](../../sport_booking/reservations/tests.py#L286) | [REQ-05](../requirements/cancel-reservation.md), [REQ-06](../requirements/approve-reservation.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_staff_can_reject_but_non_staff_cannot_decide`](../../sport_booking/reservations/tests.py#L215) | [REQ-06](../requirements/approve-reservation.md) |
| [web_views.py](../../sport_booking/reservations/web_views.py) | [`BookingForm.clean`](../../sport_booking/reservations/web_views.py#L115) | [REQ-12](../requirements/hourly-schedule.md) |
| [web_views.py](../../sport_booking/reservations/web_views.py) | [`OperatingHoursForm`](../../sport_booking/reservations/web_views.py#L27) | [REQ-13](../requirements/operating-hours.md) |
| [web_views.py](../../sport_booking/reservations/web_views.py) | [`PortalLoginView`](../../sport_booking/reservations/web_views.py#L290) | [REQ-09](../requirements/login-logout.md) |
| [web_views.py](../../sport_booking/reservations/web_views.py) | [`PortalLogoutView`](../../sport_booking/reservations/web_views.py#L295) | [REQ-09](../requirements/login-logout.md) |
| [web_views.py](../../sport_booking/reservations/web_views.py) | [`RegistrationForm`](../../sport_booking/reservations/web_views.py#L21) | [REQ-08](../requirements/customer-registration.md) |
| [web_views.py](../../sport_booking/reservations/web_views.py) | [`ScheduleFilterForm`](../../sport_booking/reservations/web_views.py#L41) | [REQ-12](../requirements/hourly-schedule.md) |
| [web_views.py](../../sport_booking/reservations/web_views.py) | [`home`](../../sport_booking/reservations/web_views.py#L138) | [REQ-07](../requirements/public-catalog.md), [REQ-10](../requirements/my-reservations.md), [REQ-11](../requirements/staff-approval-queue.md), [REQ-12](../requirements/hourly-schedule.md) |
| [web_views.py](../../sport_booking/reservations/web_views.py) | [`register`](../../sport_booking/reservations/web_views.py#L278) | [REQ-08](../requirements/customer-registration.md) |
| [web_views.py](../../sport_booking/reservations/web_views.py) | [`update_operating_hours`](../../sport_booking/reservations/web_views.py#L317) | [REQ-13](../requirements/operating-hours.md) |
