# Vazby požadavků, implementace a testů

Generováno z [traceability.json](traceability.json) příkazem `python3 scripts/update_docs.py`. Tento soubor neupravujte ručně.

Vazba na test označuje související ověření, nikoli výsledek jeho posledního běhu. Mapování vychází ze stávající dokumentace a symbolů v kódu; kontrola platnosti požadavků podle zadání je samostatný další krok.

[Požadavky](../requirements/README.md) · [Ověřování](README.md) · [Zpětné vazby z kódu a testů](#zpětné-vazby-z-kódu-a-testů)

## REQ-01

[Vytvoření rezervace](../requirements/create-reservation.md)

**Pravidla:** [BR-01](../requirements/business-rules.md#br-01), [BR-02](../requirements/business-rules.md#br-02), [BR-03](../requirements/business-rules.md#br-03), [BR-04](../requirements/business-rules.md#br-04), [BR-06](../requirements/business-rules.md#br-06), [BR-07](../requirements/business-rules.md#br-07), [BR-08](../requirements/business-rules.md#br-08), [BR-09](../requirements/business-rules.md#br-09), [BR-05](../requirements/business-rules.md#br-05)

**Návrh:** [domain-model](../design/domain-model.md)

### Implementace

- [`ReservationService.create`](../../sport_booking/reservations/services.py#L13)
- [`TimeRules.validate_interval`](../../sport_booking/reservations/rules.py#L12)
- [`DjangoDataStore.save`](../../sport_booking/reservations/persistence.py#L144)
- [`Reservation`](../../sport_booking/reservations/models.py#L35)

### Testy

- [`ReservationApiTests.test_create_succeeds_and_rejects_invalid_interval`](../../sport_booking/reservations/tests.py#L147)
- [`ReservationApiTests.test_exact_time_limits_and_exceeded_limits`](../../sport_booking/reservations/tests.py#L239)
- [`ReservationApiTests.test_authentication_ownership_and_unknown_resource`](../../sport_booking/reservations/tests.py#L222)
- [`ReservationApiTests.test_invalid_calendar_date_returns_error_without_creating`](../../sport_booking/reservations/tests.py#L234)
- [`ReservationApiTests.test_create_pending_checks_conflicts_and_inactive_resource`](../../sport_booking/reservations/tests.py#L156)
- [`CancellationNoticeTests.test_customer_cannot_choose_notice_via_api_or_web`](../../sport_booking/reservations/test_cancellation_notice.py#L180)
- [`CancellationNoticeTests.test_admin_change_affects_only_future_reservations`](../../sport_booking/reservations/test_cancellation_notice.py#L126)
- [`CancellationNoticeMigrationTests.test_existing_terms_survive_migration_and_new_creation_uses_resource_notice`](../../sport_booking/reservations/test_migrations.py#L41)

## REQ-02

[Kontrola dostupnosti](../requirements/check-availability.md)

**Pravidla:** [BR-01](../requirements/business-rules.md#br-01), [BR-02](../requirements/business-rules.md#br-02), [BR-03](../requirements/business-rules.md#br-03), [BR-04](../requirements/business-rules.md#br-04), [BR-07](../requirements/business-rules.md#br-07), [BR-09](../requirements/business-rules.md#br-09)

**Návrh:** [static-structure](../architecture/static-structure.md)

### Implementace

- [`AvailabilityQueries.check`](../../sport_booking/reservations/services.py#L109)
- [`TimeRules.has_conflict`](../../sport_booking/reservations/rules.py#L115)

### Testy

- [`ReservationApiTests.test_availability_checks_confirmed_only_and_half_open_edges`](../../sport_booking/reservations/tests.py#L170)
- [`ReservationApiTests.test_approval_request_does_not_block_until_staff_approves`](../../sport_booking/reservations/tests.py#L181)
- [`ReservationApiTests.test_inactive_resource_and_invalid_availability`](../../sport_booking/reservations/tests.py#L253)

## REQ-03

[Automatické potvrzení při vytvoření](../requirements/confirm-reservation.md)

**Pravidla:** [BR-01](../requirements/business-rules.md#br-01), [BR-02](../requirements/business-rules.md#br-02), [BR-03](../requirements/business-rules.md#br-03), [BR-04](../requirements/business-rules.md#br-04), [BR-06](../requirements/business-rules.md#br-06), [BR-08](../requirements/business-rules.md#br-08), [BR-09](../requirements/business-rules.md#br-09)

**Návrh:** [reservation-lifecycle](../design/reservation-lifecycle.md) · [design-classes](../design/design-classes.md)

### Implementace

- [`ReservationService.create`](../../sport_booking/reservations/services.py#L13)
- [`ReservationService._decide_confirmation`](../../sport_booking/reservations/services.py#L36)
- [`ReservationService._reject_competing_requests`](../../sport_booking/reservations/services.py#L30)

### Testy

- [`ReservationApiTests.test_create_succeeds_and_rejects_invalid_interval`](../../sport_booking/reservations/tests.py#L147)
- [`ReservationApiTests.test_create_pending_checks_conflicts_and_inactive_resource`](../../sport_booking/reservations/tests.py#L156)
- [`ReservationApiTests.test_automatic_creation_rejects_existing_pending_requests`](../../sport_booking/reservations/tests.py#L207)
- [`ReservationApiTests.test_confirm_endpoint_removed_and_terminal_states_cannot_reopen`](../../sport_booking/reservations/tests.py#L339)

## REQ-04

[Zabránění dvojí rezervaci](../requirements/prevent-double-booking.md)

**Pravidla:** [BR-02](../requirements/business-rules.md#br-02), [BR-06](../requirements/business-rules.md#br-06), [BR-08](../requirements/business-rules.md#br-08)

**Návrh:** [ADR-001-reservation-coordination](../architecture/decisions/ADR-001-reservation-coordination.md) · [approval-sequence](../design/approval-sequence.md)

### Implementace

- [`ReservationService._decide_confirmation`](../../sport_booking/reservations/services.py#L36)
- [`DjangoDataStore`](../../sport_booking/reservations/persistence.py#L32)

### Testy

- [`ReservationConcurrencyTests.test_conflicting_creations_commit_only_one_allocation`](../../sport_booking/reservations/test_concurrency.py#L64)
- [`ReservationConcurrencyTests.test_conflicting_approvals_commit_only_one_allocation`](../../sport_booking/reservations/test_concurrency.py#L73)
- [`ReservationConcurrencyTests.test_create_racing_approval_commits_only_one_allocation`](../../sport_booking/reservations/test_concurrency.py#L83)
- [`PersistenceFailureTests.test_failed_competitor_rejection_rolls_back_winner_and_losers`](../../sport_booking/reservations/test_architecture.py#L133)
- [`PersistenceFailureTests.test_failed_automatic_rejection_rolls_back_created_reservation`](../../sport_booking/reservations/test_architecture.py#L152)

## REQ-05

[Zrušení rezervace](../requirements/cancel-reservation.md)

**Pravidla:** [BR-02](../requirements/business-rules.md#br-02), [BR-05](../requirements/business-rules.md#br-05), [BR-06](../requirements/business-rules.md#br-06), [BR-07](../requirements/business-rules.md#br-07)

**Návrh:** [reservation-lifecycle](../design/reservation-lifecycle.md)

### Implementace

- [`ReservationService.cancel`](../../sport_booking/reservations/services.py#L78)
- [`TimeRules.validate_cancellation`](../../sport_booking/reservations/rules.py#L118)
- [`TimeRules.cancellation_deadline`](../../sport_booking/reservations/rules.py#L129)
- [`TimeRules.is_cancellation_open`](../../sport_booking/reservations/rules.py#L145)
- [`TimeRules.can_cancel`](../../sport_booking/reservations/rules.py#L136)
- [`ReservationService.create`](../../sport_booking/reservations/services.py#L13)
- [`Resource`](../../sport_booking/reservations/models.py#L13)
- [`Reservation`](../../sport_booking/reservations/models.py#L35)
- [`Reservation`](../../sport_booking/reservations/domain.py#L85)
- [`ReservationListing`](../../sport_booking/reservations/domain.py#L33)
- [`Resource`](../../sport_booking/reservations/domain.py#L48)
- [`DjangoDataStore.load_protected`](../../sport_booking/reservations/persistence.py#L76)
- [`DjangoDataStore.load_resource`](../../sport_booking/reservations/persistence.py#L58)
- [`DjangoDataStore.save`](../../sport_booking/reservations/persistence.py#L144)
- [`ResourceAdmin`](../../sport_booking/reservations/admin.py#L13)
- [`ReservationAdmin`](../../sport_booking/reservations/admin.py#L25)
- [`TimeRules.cancellation_deadline_label`](../../sport_booking/reservations/rules.py#L149)
- [`ReservationEndpoint.cancel`](../../sport_booking/reservations/api.py#L102)

### Testy

- [`ReservationApiTests.test_cancel_confirmed_releases_resource_and_rejects_repeat`](../../sport_booking/reservations/tests.py#L263)
- [`ReservationApiTests.test_owner_can_cancel_pending_approval_but_not_after_start`](../../sport_booking/reservations/tests.py#L269)
- [`ReservationApiTests.test_expiry_exact_deadline_on_approve_cancel_and_command`](../../sport_booking/reservations/tests.py#L305)
- [`ReservationApiTests.test_pending_request_remains_actionable_after_24_hours_until_start`](../../sport_booking/reservations/tests.py#L287)
- [`ReservationConcurrencyTests.test_approve_racing_cancel_finishes_cancelled`](../../sport_booking/reservations/test_concurrency.py#L95)
- [`CancellationNoticeTests.test_cancellation_exact_boundaries_for_multiple_notices`](../../sport_booking/reservations/test_cancellation_notice.py#L72)
- [`CancellationNoticeTests.test_zero_notice_and_started_reservations`](../../sport_booking/reservations/test_cancellation_notice.py#L89)
- [`CancellationNoticeTests.test_pending_can_be_withdrawn_until_start_then_expires`](../../sport_booking/reservations/test_cancellation_notice.py#L102)
- [`CancellationNoticeTests.test_admin_change_affects_only_future_reservations`](../../sport_booking/reservations/test_cancellation_notice.py#L126)
- [`CancellationNoticeTests.test_approval_preserves_saved_notice_after_configuration_change`](../../sport_booking/reservations/test_cancellation_notice.py#L140)
- [`CancellationNoticeTests.test_invalid_or_unauthorized_setting_does_not_change_resource`](../../sport_booking/reservations/test_cancellation_notice.py#L160)
- [`CancellationNoticeTests.test_customer_cannot_choose_notice_via_api_or_web`](../../sport_booking/reservations/test_cancellation_notice.py#L180)
- [`CancellationNoticeTests.test_stale_web_page_cannot_bypass_deadline`](../../sport_booking/reservations/test_cancellation_notice.py#L187)
- [`CancellationNoticeTests.test_web_notice_and_read_only_listing_use_saved_value`](../../sport_booking/reservations/test_cancellation_notice.py#L201)
- [`CancellationNoticeTests.test_late_cancellation_keeps_allocation_and_rejected_competitors`](../../sport_booking/reservations/test_cancellation_notice.py#L211)
- [`CancellationNoticeTests.test_saved_notice_is_read_only_in_reservation_admin`](../../sport_booking/reservations/test_cancellation_notice.py#L231)
- [`CancellationNoticeTests.test_both_serial_orders_of_approval_and_cancellation_after_deadline`](../../sport_booking/reservations/test_cancellation_notice.py#L240)
- [`CancellationNoticeTests.test_cancellation_failure_rolls_back_status_and_saved_notice`](../../sport_booking/reservations/test_cancellation_notice.py#L258)
- [`CancellationNoticeTests.test_ownership_authentication_and_repeat_preserve_saved_terms`](../../sport_booking/reservations/test_cancellation_notice.py#L267)
- [`CancellationNoticeTests.test_dst_deadline_is_displayed_in_correct_local_offset`](../../sport_booking/reservations/test_cancellation_notice.py#L279)
- [`CancellationClockTests.test_dst_uses_elapsed_utc_minutes_and_shared_display_rule`](../../sport_booking/reservations/test_cancellation_notice.py#L299)
- [`CancellationClockTests.test_large_valid_notice_does_not_overflow_deadline`](../../sport_booking/reservations/test_cancellation_notice.py#L318)
- [`CancellationBaselineTests.test_cancel_one_second_before_start`](../../sport_booking/reservations/test_c08_baseline.py#L66)
- [`CancellationBaselineTests.test_refuse_cancel_at_start`](../../sport_booking/reservations/test_c08_baseline.py#L69)
- [`CancellationNoticeMigrationTests.test_existing_terms_survive_migration_and_new_creation_uses_resource_notice`](../../sport_booking/reservations/test_migrations.py#L41)
- [`ReservationConcurrencyTests.test_approve_racing_cancel_after_notice_deadline_has_serial_outcome`](../../sport_booking/reservations/test_concurrency.py#L106)
- [`ReservationConcurrencyTests.test_notice_change_racing_creation_saves_one_committed_setting`](../../sport_booking/reservations/test_concurrency.py#L119)

## REQ-06

[Schválení rezervace](../requirements/approve-reservation.md)

**Pravidla:** [BR-01](../requirements/business-rules.md#br-01), [BR-02](../requirements/business-rules.md#br-02), [BR-03](../requirements/business-rules.md#br-03), [BR-04](../requirements/business-rules.md#br-04), [BR-06](../requirements/business-rules.md#br-06), [BR-07](../requirements/business-rules.md#br-07), [BR-08](../requirements/business-rules.md#br-08), [BR-09](../requirements/business-rules.md#br-09)

**Návrh:** [approval-sequence](../design/approval-sequence.md) · [reservation-lifecycle](../design/reservation-lifecycle.md) · [detailed-design](../design/detailed-design.md)

### Implementace

- [`ReservationService.approve`](../../sport_booking/reservations/services.py#L57)
- [`ReservationService._expire_if_due`](../../sport_booking/reservations/services.py#L49)
- [`ReservationService.expire_due`](../../sport_booking/reservations/services.py#L90)
- [`IdentityAccess.require_approver`](../../sport_booking/reservations/identity.py#L22)
- [`ReservationService._reject_competing_requests`](../../sport_booking/reservations/services.py#L30)
- [`DjangoDataStore.overlapping_pending_ids`](../../sport_booking/reservations/persistence.py#L96)

### Testy

- [`ReservationApiTests.test_delayed_approval_succeeds_after_24_hours_before_start`](../../sport_booking/reservations/tests.py#L280)
- [`ReservationApiTests.test_staff_can_reject_but_non_staff_cannot_decide`](../../sport_booking/reservations/tests.py#L216)
- [`ReservationApiTests.test_expiry_exact_deadline_on_approve_cancel_and_command`](../../sport_booking/reservations/tests.py#L305)
- [`ReservationApiTests.test_pending_request_remains_actionable_after_24_hours_until_start`](../../sport_booking/reservations/tests.py#L287)
- [`ReservationApiTests.test_confirmation_rejects_only_overlapping_pending_same_resource`](../../sport_booking/reservations/tests.py#L192)
- [`ReservationApiTests.test_invalid_approval_decision_is_rejected_without_state_change`](../../sport_booking/reservations/tests.py#L332)

## REQ-07

[Veřejný katalog sportovišť](../requirements/public-catalog.md)

**Pravidla:** Podmínky a oprávnění jsou uvedené přímo u požadavku.

**Návrh:** [web-portal](../design/web-portal.md)

### Implementace

- [`home`](../../sport_booking/reservations/web_views.py#L138)
- [`PortalQueries.resources`](../../sport_booking/reservations/portal.py#L12)
- [`DjangoDataStore.list_resources`](../../sport_booking/reservations/persistence.py#L110)

### Testy

- [`PortalRequirementTests.test_public_catalog_shows_metadata_and_operating_availability`](../../sport_booking/reservations/test_portal_requirements.py#L41)
- [`PortalRequirementTests.test_empty_public_catalog_is_displayed_without_error`](../../sport_booking/reservations/test_portal_requirements.py#L52)
- [`PortalRequirementTests.test_guest_and_customer_cannot_see_staff_queue`](../../sport_booking/reservations/test_portal_requirements.py#L177)

## REQ-08

[Registrace zákazníka](../requirements/customer-registration.md)

**Pravidla:** Podmínky a oprávnění jsou uvedené přímo u požadavku.

**Návrh:** [web-portal](../design/web-portal.md)

### Implementace

- [`RegistrationForm`](../../sport_booking/reservations/web_views.py#L21)
- [`register`](../../sport_booking/reservations/web_views.py#L280)

### Testy

- [`PortalRequirementTests.test_registration_creates_only_customer_and_authenticates`](../../sport_booking/reservations/test_portal_requirements.py#L59)
- [`PortalRequirementTests.test_invalid_registration_does_not_create_or_authenticate_user`](../../sport_booking/reservations/test_portal_requirements.py#L76)
- [`PortalRequirementTests.test_authenticated_user_cannot_create_second_account`](../../sport_booking/reservations/test_portal_requirements.py#L93)
- [`PortalRequirementTests.test_account_forms_require_csrf`](../../sport_booking/reservations/test_portal_requirements.py#L142)
- [`PortalRequirementTests.test_account_forms_work_with_valid_csrf_tokens`](../../sport_booking/reservations/test_portal_requirements.py#L238)

## REQ-09

[Přihlášení a odhlášení](../requirements/login-logout.md)

**Pravidla:** Podmínky a oprávnění jsou uvedené přímo u požadavku.

**Návrh:** [web-portal](../design/web-portal.md)

### Implementace

- [`PortalLoginView`](../../sport_booking/reservations/web_views.py#L292)
- [`PortalLogoutView`](../../sport_booking/reservations/web_views.py#L297)

### Testy

- [`PortalRequirementTests.test_login_accepts_active_customer_and_staff`](../../sport_booking/reservations/test_portal_requirements.py#L103)
- [`PortalRequirementTests.test_login_rejects_invalid_credentials_and_inactive_account`](../../sport_booking/reservations/test_portal_requirements.py#L113)
- [`PortalRequirementTests.test_login_does_not_redirect_to_untrusted_host`](../../sport_booking/reservations/test_portal_requirements.py#L127)
- [`PortalRequirementTests.test_logout_requires_post_and_ends_session`](../../sport_booking/reservations/test_portal_requirements.py#L133)
- [`PortalRequirementTests.test_account_forms_require_csrf`](../../sport_booking/reservations/test_portal_requirements.py#L142)
- [`PortalRequirementTests.test_account_forms_work_with_valid_csrf_tokens`](../../sport_booking/reservations/test_portal_requirements.py#L238)

## REQ-10

[Zobrazení vlastních rezervací](../requirements/my-reservations.md)

**Pravidla:** [BR-05](../requirements/business-rules.md#br-05), [BR-07](../requirements/business-rules.md#br-07)

**Návrh:** [web-portal](../design/web-portal.md)

### Implementace

- [`home`](../../sport_booking/reservations/web_views.py#L138)
- [`PortalQueries.reservations_for_user`](../../sport_booking/reservations/portal.py#L16)
- [`DjangoDataStore.list_reservations`](../../sport_booking/reservations/persistence.py#L121)
- [`DjangoDataStore._reservation_listings`](../../sport_booking/reservations/persistence.py#L133)
- [`TimeRules.display_status`](../../sport_booking/reservations/rules.py#L107)
- [`TimeRules.cancellation_deadline`](../../sport_booking/reservations/rules.py#L129)
- [`TimeRules.can_cancel`](../../sport_booking/reservations/rules.py#L136)
- [`TimeRules.cancellation_deadline_label`](../../sport_booking/reservations/rules.py#L149)

### Testy

- [`PortalRequirementTests.test_customer_sees_only_own_reservations_in_all_five_states`](../../sport_booking/reservations/test_portal_requirements.py#L152)
- [`PortalRequirementTests.test_staff_personal_list_still_contains_only_own_reservations`](../../sport_booking/reservations/test_portal_requirements.py#L170)
- [`PortalRequirementTests.test_customer_with_no_reservations_sees_empty_state`](../../sport_booking/reservations/test_portal_requirements.py#L190)
- [`PortalRequirementTests.test_guest_and_customer_cannot_see_staff_queue`](../../sport_booking/reservations/test_portal_requirements.py#L177)
- [`PortalRequirementTests.test_personal_list_displays_effective_expiry_without_writing_database`](../../sport_booking/reservations/test_portal_requirements.py#L226)
- [`CancellationNoticeTests.test_web_notice_and_read_only_listing_use_saved_value`](../../sport_booking/reservations/test_cancellation_notice.py#L201)
- [`CancellationNoticeTests.test_stale_web_page_cannot_bypass_deadline`](../../sport_booking/reservations/test_cancellation_notice.py#L187)
- [`CancellationNoticeTests.test_dst_deadline_is_displayed_in_correct_local_offset`](../../sport_booking/reservations/test_cancellation_notice.py#L279)

## REQ-11

[Přehled čekajících žádostí správce](../requirements/staff-approval-queue.md)

**Pravidla:** [BR-07](../requirements/business-rules.md#br-07)

**Návrh:** [web-portal](../design/web-portal.md)

### Implementace

- [`home`](../../sport_booking/reservations/web_views.py#L138)
- [`PortalQueries.pending_reservations`](../../sport_booking/reservations/portal.py#L28)
- [`DjangoDataStore.list_pending_reservations`](../../sport_booking/reservations/persistence.py#L125)

### Testy

- [`PortalRequirementTests.test_guest_and_customer_cannot_see_staff_queue`](../../sport_booking/reservations/test_portal_requirements.py#L177)
- [`PortalRequirementTests.test_staff_queue_shows_only_pending_before_start_without_mutation`](../../sport_booking/reservations/test_portal_requirements.py#L197)
- [`PortalRequirementTests.test_staff_queue_displays_empty_state`](../../sport_booking/reservations/test_portal_requirements.py#L220)
- [`PortalTests.test_non_staff_cannot_approve_pending_reservation`](../../sport_booking/reservations/test_portal.py#L103)

## REQ-12

[Výběr rezervace z hodinového rozvrhu](../requirements/hourly-schedule.md)

**Pravidla:** [BR-01](../requirements/business-rules.md#br-01), [BR-02](../requirements/business-rules.md#br-02), [BR-03](../requirements/business-rules.md#br-03), [BR-04](../requirements/business-rules.md#br-04), [BR-07](../requirements/business-rules.md#br-07), [BR-09](../requirements/business-rules.md#br-09)

**Návrh:** [hourly-schedule](../design/hourly-schedule.md)

### Implementace

- [`ScheduleFilterForm`](../../sport_booking/reservations/web_views.py#L41)
- [`BookingForm.clean`](../../sport_booking/reservations/web_views.py#L115)
- [`home`](../../sport_booking/reservations/web_views.py#L138)
- [`PortalQueries.weekly_schedule`](../../sport_booking/reservations/portal.py#L38)
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
- [`ScheduleTests.test_pending_other_resource_and_cancelled_do_not_block`](../../sport_booking/reservations/test_schedule.py#L132)
- [`ScheduleTests.test_approval_required_resource_creates_pending_from_blocks`](../../sport_booking/reservations/test_schedule.py#L143)
- [`ScheduleTests.test_stale_schedule_does_not_bypass_atomic_conflict_check`](../../sport_booking/reservations/test_schedule.py#L151)
- [`ScheduleTests.test_invalid_resource_and_day_do_not_create_reservation`](../../sport_booking/reservations/test_schedule.py#L162)
- [`ScheduleTests.test_past_and_beyond_thirty_days_are_disabled`](../../sport_booking/reservations/test_schedule.py#L171)
- [`ScheduleTests.test_availability_from_blocks_is_read_only`](../../sport_booking/reservations/test_schedule.py#L179)
- [`ScheduleTests.test_manual_input_keeps_two_hour_server_limit`](../../sport_booking/reservations/test_schedule.py#L183)
- [`ScheduleTests.test_guest_cannot_submit_grid_booking`](../../sport_booking/reservations/test_schedule.py#L194)
- [`ScheduleTests.test_slot_interval_is_derived_on_server_not_client_values`](../../sport_booking/reservations/test_schedule.py#L199)
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
- [`update_operating_hours`](../../sport_booking/reservations/web_views.py#L320)
- [`ResourceService.update_operating_hours`](../../sport_booking/reservations/services.py#L126)
- [`ReservationService._decide_confirmation`](../../sport_booking/reservations/services.py#L36)
- [`AvailabilityQueries.check`](../../sport_booking/reservations/services.py#L109)
- [`TimeRules.validate_operating_hours`](../../sport_booking/reservations/rules.py#L27)
- [`TimeRules.is_within_operating_hours`](../../sport_booking/reservations/rules.py#L31)
- [`DjangoDataStore.set_operating_hours`](../../sport_booking/reservations/persistence.py#L71)
- [`Resource.clean`](../../sport_booking/reservations/models.py#L26)

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
| [admin.py](../../sport_booking/reservations/admin.py) | [`ReservationAdmin`](../../sport_booking/reservations/admin.py#L25) | [REQ-05](../requirements/cancel-reservation.md) |
| [admin.py](../../sport_booking/reservations/admin.py) | [`ResourceAdmin`](../../sport_booking/reservations/admin.py#L13) | [REQ-05](../requirements/cancel-reservation.md) |
| [api.py](../../sport_booking/reservations/api.py) | [`ReservationEndpoint.cancel`](../../sport_booking/reservations/api.py#L102) | [REQ-05](../requirements/cancel-reservation.md) |
| [domain.py](../../sport_booking/reservations/domain.py) | [`Reservation`](../../sport_booking/reservations/domain.py#L85) | [REQ-05](../requirements/cancel-reservation.md) |
| [domain.py](../../sport_booking/reservations/domain.py) | [`ReservationListing`](../../sport_booking/reservations/domain.py#L33) | [REQ-05](../requirements/cancel-reservation.md) |
| [domain.py](../../sport_booking/reservations/domain.py) | [`Resource`](../../sport_booking/reservations/domain.py#L48) | [REQ-05](../requirements/cancel-reservation.md) |
| [identity.py](../../sport_booking/reservations/identity.py) | [`IdentityAccess.require_approver`](../../sport_booking/reservations/identity.py#L22) | [REQ-06](../requirements/approve-reservation.md) |
| [models.py](../../sport_booking/reservations/models.py) | [`Reservation`](../../sport_booking/reservations/models.py#L35) | [REQ-01](../requirements/create-reservation.md), [REQ-05](../requirements/cancel-reservation.md) |
| [models.py](../../sport_booking/reservations/models.py) | [`Resource`](../../sport_booking/reservations/models.py#L13) | [REQ-05](../requirements/cancel-reservation.md) |
| [models.py](../../sport_booking/reservations/models.py) | [`Resource.clean`](../../sport_booking/reservations/models.py#L26) | [REQ-13](../requirements/operating-hours.md) |
| [persistence.py](../../sport_booking/reservations/persistence.py) | [`DjangoDataStore`](../../sport_booking/reservations/persistence.py#L32) | [REQ-04](../requirements/prevent-double-booking.md) |
| [persistence.py](../../sport_booking/reservations/persistence.py) | [`DjangoDataStore._reservation_listings`](../../sport_booking/reservations/persistence.py#L133) | [REQ-10](../requirements/my-reservations.md) |
| [persistence.py](../../sport_booking/reservations/persistence.py) | [`DjangoDataStore.list_pending_reservations`](../../sport_booking/reservations/persistence.py#L125) | [REQ-11](../requirements/staff-approval-queue.md) |
| [persistence.py](../../sport_booking/reservations/persistence.py) | [`DjangoDataStore.list_reservations`](../../sport_booking/reservations/persistence.py#L121) | [REQ-10](../requirements/my-reservations.md) |
| [persistence.py](../../sport_booking/reservations/persistence.py) | [`DjangoDataStore.list_resources`](../../sport_booking/reservations/persistence.py#L110) | [REQ-07](../requirements/public-catalog.md) |
| [persistence.py](../../sport_booking/reservations/persistence.py) | [`DjangoDataStore.load_protected`](../../sport_booking/reservations/persistence.py#L76) | [REQ-05](../requirements/cancel-reservation.md) |
| [persistence.py](../../sport_booking/reservations/persistence.py) | [`DjangoDataStore.load_resource`](../../sport_booking/reservations/persistence.py#L58) | [REQ-05](../requirements/cancel-reservation.md) |
| [persistence.py](../../sport_booking/reservations/persistence.py) | [`DjangoDataStore.overlapping_pending_ids`](../../sport_booking/reservations/persistence.py#L96) | [REQ-06](../requirements/approve-reservation.md) |
| [persistence.py](../../sport_booking/reservations/persistence.py) | [`DjangoDataStore.save`](../../sport_booking/reservations/persistence.py#L144) | [REQ-01](../requirements/create-reservation.md), [REQ-05](../requirements/cancel-reservation.md) |
| [persistence.py](../../sport_booking/reservations/persistence.py) | [`DjangoDataStore.set_operating_hours`](../../sport_booking/reservations/persistence.py#L71) | [REQ-13](../requirements/operating-hours.md) |
| [portal.py](../../sport_booking/reservations/portal.py) | [`PortalQueries.pending_reservations`](../../sport_booking/reservations/portal.py#L28) | [REQ-11](../requirements/staff-approval-queue.md) |
| [portal.py](../../sport_booking/reservations/portal.py) | [`PortalQueries.reservations_for_user`](../../sport_booking/reservations/portal.py#L16) | [REQ-10](../requirements/my-reservations.md) |
| [portal.py](../../sport_booking/reservations/portal.py) | [`PortalQueries.resources`](../../sport_booking/reservations/portal.py#L12) | [REQ-07](../requirements/public-catalog.md) |
| [portal.py](../../sport_booking/reservations/portal.py) | [`PortalQueries.weekly_schedule`](../../sport_booking/reservations/portal.py#L38) | [REQ-12](../requirements/hourly-schedule.md) |
| [rules.py](../../sport_booking/reservations/rules.py) | [`TimeRules.can_cancel`](../../sport_booking/reservations/rules.py#L136) | [REQ-05](../requirements/cancel-reservation.md), [REQ-10](../requirements/my-reservations.md) |
| [rules.py](../../sport_booking/reservations/rules.py) | [`TimeRules.cancellation_deadline`](../../sport_booking/reservations/rules.py#L129) | [REQ-05](../requirements/cancel-reservation.md), [REQ-10](../requirements/my-reservations.md) |
| [rules.py](../../sport_booking/reservations/rules.py) | [`TimeRules.cancellation_deadline_label`](../../sport_booking/reservations/rules.py#L149) | [REQ-05](../requirements/cancel-reservation.md), [REQ-10](../requirements/my-reservations.md) |
| [rules.py](../../sport_booking/reservations/rules.py) | [`TimeRules.display_status`](../../sport_booking/reservations/rules.py#L107) | [REQ-10](../requirements/my-reservations.md) |
| [rules.py](../../sport_booking/reservations/rules.py) | [`TimeRules.has_conflict`](../../sport_booking/reservations/rules.py#L115) | [REQ-02](../requirements/check-availability.md) |
| [rules.py](../../sport_booking/reservations/rules.py) | [`TimeRules.is_cancellation_open`](../../sport_booking/reservations/rules.py#L145) | [REQ-05](../requirements/cancel-reservation.md) |
| [rules.py](../../sport_booking/reservations/rules.py) | [`TimeRules.is_within_operating_hours`](../../sport_booking/reservations/rules.py#L31) | [REQ-13](../requirements/operating-hours.md) |
| [rules.py](../../sport_booking/reservations/rules.py) | [`TimeRules.validate_cancellation`](../../sport_booking/reservations/rules.py#L118) | [REQ-05](../requirements/cancel-reservation.md) |
| [rules.py](../../sport_booking/reservations/rules.py) | [`TimeRules.validate_interval`](../../sport_booking/reservations/rules.py#L12) | [REQ-01](../requirements/create-reservation.md), [REQ-12](../requirements/hourly-schedule.md) |
| [rules.py](../../sport_booking/reservations/rules.py) | [`TimeRules.validate_operating_hours`](../../sport_booking/reservations/rules.py#L27) | [REQ-13](../requirements/operating-hours.md) |
| [rules.py](../../sport_booking/reservations/rules.py) | [`TimeRules.weekly_blocks`](../../sport_booking/reservations/rules.py#L72) | [REQ-12](../requirements/hourly-schedule.md) |
| [services.py](../../sport_booking/reservations/services.py) | [`AvailabilityQueries.check`](../../sport_booking/reservations/services.py#L109) | [REQ-02](../requirements/check-availability.md), [REQ-13](../requirements/operating-hours.md) |
| [services.py](../../sport_booking/reservations/services.py) | [`ReservationService._decide_confirmation`](../../sport_booking/reservations/services.py#L36) | [REQ-03](../requirements/confirm-reservation.md), [REQ-04](../requirements/prevent-double-booking.md), [REQ-13](../requirements/operating-hours.md) |
| [services.py](../../sport_booking/reservations/services.py) | [`ReservationService._expire_if_due`](../../sport_booking/reservations/services.py#L49) | [REQ-06](../requirements/approve-reservation.md) |
| [services.py](../../sport_booking/reservations/services.py) | [`ReservationService._reject_competing_requests`](../../sport_booking/reservations/services.py#L30) | [REQ-03](../requirements/confirm-reservation.md), [REQ-06](../requirements/approve-reservation.md) |
| [services.py](../../sport_booking/reservations/services.py) | [`ReservationService.approve`](../../sport_booking/reservations/services.py#L57) | [REQ-06](../requirements/approve-reservation.md) |
| [services.py](../../sport_booking/reservations/services.py) | [`ReservationService.cancel`](../../sport_booking/reservations/services.py#L78) | [REQ-05](../requirements/cancel-reservation.md) |
| [services.py](../../sport_booking/reservations/services.py) | [`ReservationService.create`](../../sport_booking/reservations/services.py#L13) | [REQ-01](../requirements/create-reservation.md), [REQ-03](../requirements/confirm-reservation.md), [REQ-05](../requirements/cancel-reservation.md), [REQ-12](../requirements/hourly-schedule.md) |
| [services.py](../../sport_booking/reservations/services.py) | [`ReservationService.expire_due`](../../sport_booking/reservations/services.py#L90) | [REQ-06](../requirements/approve-reservation.md) |
| [services.py](../../sport_booking/reservations/services.py) | [`ResourceService.update_operating_hours`](../../sport_booking/reservations/services.py#L126) | [REQ-13](../requirements/operating-hours.md) |
| [app.css](../../sport_booking/reservations/static/reservations/app.css) | [`app.css`](../../sport_booking/reservations/static/reservations/app.css) | [REQ-12](../requirements/hourly-schedule.md) |
| [schedule.js](../../sport_booking/reservations/static/reservations/schedule.js) | [`schedule.js`](../../sport_booking/reservations/static/reservations/schedule.js) | [REQ-12](../requirements/hourly-schedule.md) |
| [home.html](../../sport_booking/reservations/templates/reservations/home.html) | [`home.html`](../../sport_booking/reservations/templates/reservations/home.html) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_architecture.py](../../sport_booking/reservations/test_architecture.py) | [`PersistenceFailureTests.test_failed_automatic_rejection_rolls_back_created_reservation`](../../sport_booking/reservations/test_architecture.py#L152) | [REQ-04](../requirements/prevent-double-booking.md) |
| [test_architecture.py](../../sport_booking/reservations/test_architecture.py) | [`PersistenceFailureTests.test_failed_competitor_rejection_rolls_back_winner_and_losers`](../../sport_booking/reservations/test_architecture.py#L133) | [REQ-04](../requirements/prevent-double-booking.md) |
| [test_c08_baseline.py](../../sport_booking/reservations/test_c08_baseline.py) | [`CancellationBaselineTests.test_cancel_one_second_before_start`](../../sport_booking/reservations/test_c08_baseline.py#L66) | [REQ-05](../requirements/cancel-reservation.md) |
| [test_c08_baseline.py](../../sport_booking/reservations/test_c08_baseline.py) | [`CancellationBaselineTests.test_refuse_cancel_at_start`](../../sport_booking/reservations/test_c08_baseline.py#L69) | [REQ-05](../requirements/cancel-reservation.md) |
| [test_cancellation_notice.py](../../sport_booking/reservations/test_cancellation_notice.py) | [`CancellationClockTests.test_dst_uses_elapsed_utc_minutes_and_shared_display_rule`](../../sport_booking/reservations/test_cancellation_notice.py#L299) | [REQ-05](../requirements/cancel-reservation.md) |
| [test_cancellation_notice.py](../../sport_booking/reservations/test_cancellation_notice.py) | [`CancellationClockTests.test_large_valid_notice_does_not_overflow_deadline`](../../sport_booking/reservations/test_cancellation_notice.py#L318) | [REQ-05](../requirements/cancel-reservation.md) |
| [test_cancellation_notice.py](../../sport_booking/reservations/test_cancellation_notice.py) | [`CancellationNoticeTests.test_admin_change_affects_only_future_reservations`](../../sport_booking/reservations/test_cancellation_notice.py#L126) | [REQ-01](../requirements/create-reservation.md), [REQ-05](../requirements/cancel-reservation.md) |
| [test_cancellation_notice.py](../../sport_booking/reservations/test_cancellation_notice.py) | [`CancellationNoticeTests.test_approval_preserves_saved_notice_after_configuration_change`](../../sport_booking/reservations/test_cancellation_notice.py#L140) | [REQ-05](../requirements/cancel-reservation.md) |
| [test_cancellation_notice.py](../../sport_booking/reservations/test_cancellation_notice.py) | [`CancellationNoticeTests.test_both_serial_orders_of_approval_and_cancellation_after_deadline`](../../sport_booking/reservations/test_cancellation_notice.py#L240) | [REQ-05](../requirements/cancel-reservation.md) |
| [test_cancellation_notice.py](../../sport_booking/reservations/test_cancellation_notice.py) | [`CancellationNoticeTests.test_cancellation_exact_boundaries_for_multiple_notices`](../../sport_booking/reservations/test_cancellation_notice.py#L72) | [REQ-05](../requirements/cancel-reservation.md) |
| [test_cancellation_notice.py](../../sport_booking/reservations/test_cancellation_notice.py) | [`CancellationNoticeTests.test_cancellation_failure_rolls_back_status_and_saved_notice`](../../sport_booking/reservations/test_cancellation_notice.py#L258) | [REQ-05](../requirements/cancel-reservation.md) |
| [test_cancellation_notice.py](../../sport_booking/reservations/test_cancellation_notice.py) | [`CancellationNoticeTests.test_customer_cannot_choose_notice_via_api_or_web`](../../sport_booking/reservations/test_cancellation_notice.py#L180) | [REQ-01](../requirements/create-reservation.md), [REQ-05](../requirements/cancel-reservation.md) |
| [test_cancellation_notice.py](../../sport_booking/reservations/test_cancellation_notice.py) | [`CancellationNoticeTests.test_dst_deadline_is_displayed_in_correct_local_offset`](../../sport_booking/reservations/test_cancellation_notice.py#L279) | [REQ-05](../requirements/cancel-reservation.md), [REQ-10](../requirements/my-reservations.md) |
| [test_cancellation_notice.py](../../sport_booking/reservations/test_cancellation_notice.py) | [`CancellationNoticeTests.test_invalid_or_unauthorized_setting_does_not_change_resource`](../../sport_booking/reservations/test_cancellation_notice.py#L160) | [REQ-05](../requirements/cancel-reservation.md) |
| [test_cancellation_notice.py](../../sport_booking/reservations/test_cancellation_notice.py) | [`CancellationNoticeTests.test_late_cancellation_keeps_allocation_and_rejected_competitors`](../../sport_booking/reservations/test_cancellation_notice.py#L211) | [REQ-05](../requirements/cancel-reservation.md) |
| [test_cancellation_notice.py](../../sport_booking/reservations/test_cancellation_notice.py) | [`CancellationNoticeTests.test_ownership_authentication_and_repeat_preserve_saved_terms`](../../sport_booking/reservations/test_cancellation_notice.py#L267) | [REQ-05](../requirements/cancel-reservation.md) |
| [test_cancellation_notice.py](../../sport_booking/reservations/test_cancellation_notice.py) | [`CancellationNoticeTests.test_pending_can_be_withdrawn_until_start_then_expires`](../../sport_booking/reservations/test_cancellation_notice.py#L102) | [REQ-05](../requirements/cancel-reservation.md) |
| [test_cancellation_notice.py](../../sport_booking/reservations/test_cancellation_notice.py) | [`CancellationNoticeTests.test_saved_notice_is_read_only_in_reservation_admin`](../../sport_booking/reservations/test_cancellation_notice.py#L231) | [REQ-05](../requirements/cancel-reservation.md) |
| [test_cancellation_notice.py](../../sport_booking/reservations/test_cancellation_notice.py) | [`CancellationNoticeTests.test_stale_web_page_cannot_bypass_deadline`](../../sport_booking/reservations/test_cancellation_notice.py#L187) | [REQ-05](../requirements/cancel-reservation.md), [REQ-10](../requirements/my-reservations.md) |
| [test_cancellation_notice.py](../../sport_booking/reservations/test_cancellation_notice.py) | [`CancellationNoticeTests.test_web_notice_and_read_only_listing_use_saved_value`](../../sport_booking/reservations/test_cancellation_notice.py#L201) | [REQ-05](../requirements/cancel-reservation.md), [REQ-10](../requirements/my-reservations.md) |
| [test_cancellation_notice.py](../../sport_booking/reservations/test_cancellation_notice.py) | [`CancellationNoticeTests.test_zero_notice_and_started_reservations`](../../sport_booking/reservations/test_cancellation_notice.py#L89) | [REQ-05](../requirements/cancel-reservation.md) |
| [test_concurrency.py](../../sport_booking/reservations/test_concurrency.py) | [`ReservationConcurrencyTests.test_approve_racing_cancel_after_notice_deadline_has_serial_outcome`](../../sport_booking/reservations/test_concurrency.py#L106) | [REQ-05](../requirements/cancel-reservation.md) |
| [test_concurrency.py](../../sport_booking/reservations/test_concurrency.py) | [`ReservationConcurrencyTests.test_approve_racing_cancel_finishes_cancelled`](../../sport_booking/reservations/test_concurrency.py#L95) | [REQ-05](../requirements/cancel-reservation.md) |
| [test_concurrency.py](../../sport_booking/reservations/test_concurrency.py) | [`ReservationConcurrencyTests.test_conflicting_approvals_commit_only_one_allocation`](../../sport_booking/reservations/test_concurrency.py#L73) | [REQ-04](../requirements/prevent-double-booking.md) |
| [test_concurrency.py](../../sport_booking/reservations/test_concurrency.py) | [`ReservationConcurrencyTests.test_conflicting_creations_commit_only_one_allocation`](../../sport_booking/reservations/test_concurrency.py#L64) | [REQ-04](../requirements/prevent-double-booking.md) |
| [test_concurrency.py](../../sport_booking/reservations/test_concurrency.py) | [`ReservationConcurrencyTests.test_create_racing_approval_commits_only_one_allocation`](../../sport_booking/reservations/test_concurrency.py#L83) | [REQ-04](../requirements/prevent-double-booking.md) |
| [test_concurrency.py](../../sport_booking/reservations/test_concurrency.py) | [`ReservationConcurrencyTests.test_notice_change_racing_creation_saves_one_committed_setting`](../../sport_booking/reservations/test_concurrency.py#L119) | [REQ-05](../requirements/cancel-reservation.md) |
| [test_migrations.py](../../sport_booking/reservations/test_migrations.py) | [`CancellationNoticeMigrationTests.test_existing_terms_survive_migration_and_new_creation_uses_resource_notice`](../../sport_booking/reservations/test_migrations.py#L41) | [REQ-01](../requirements/create-reservation.md), [REQ-05](../requirements/cancel-reservation.md) |
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
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_account_forms_require_csrf`](../../sport_booking/reservations/test_portal_requirements.py#L142) | [REQ-08](../requirements/customer-registration.md), [REQ-09](../requirements/login-logout.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_account_forms_work_with_valid_csrf_tokens`](../../sport_booking/reservations/test_portal_requirements.py#L238) | [REQ-08](../requirements/customer-registration.md), [REQ-09](../requirements/login-logout.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_authenticated_user_cannot_create_second_account`](../../sport_booking/reservations/test_portal_requirements.py#L93) | [REQ-08](../requirements/customer-registration.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_customer_sees_only_own_reservations_in_all_five_states`](../../sport_booking/reservations/test_portal_requirements.py#L152) | [REQ-10](../requirements/my-reservations.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_customer_with_no_reservations_sees_empty_state`](../../sport_booking/reservations/test_portal_requirements.py#L190) | [REQ-10](../requirements/my-reservations.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_empty_public_catalog_is_displayed_without_error`](../../sport_booking/reservations/test_portal_requirements.py#L52) | [REQ-07](../requirements/public-catalog.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_guest_and_customer_cannot_see_staff_queue`](../../sport_booking/reservations/test_portal_requirements.py#L177) | [REQ-07](../requirements/public-catalog.md), [REQ-10](../requirements/my-reservations.md), [REQ-11](../requirements/staff-approval-queue.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_invalid_registration_does_not_create_or_authenticate_user`](../../sport_booking/reservations/test_portal_requirements.py#L76) | [REQ-08](../requirements/customer-registration.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_login_accepts_active_customer_and_staff`](../../sport_booking/reservations/test_portal_requirements.py#L103) | [REQ-09](../requirements/login-logout.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_login_does_not_redirect_to_untrusted_host`](../../sport_booking/reservations/test_portal_requirements.py#L127) | [REQ-09](../requirements/login-logout.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_login_rejects_invalid_credentials_and_inactive_account`](../../sport_booking/reservations/test_portal_requirements.py#L113) | [REQ-09](../requirements/login-logout.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_logout_requires_post_and_ends_session`](../../sport_booking/reservations/test_portal_requirements.py#L133) | [REQ-09](../requirements/login-logout.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_personal_list_displays_effective_expiry_without_writing_database`](../../sport_booking/reservations/test_portal_requirements.py#L226) | [REQ-10](../requirements/my-reservations.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_public_catalog_shows_metadata_and_operating_availability`](../../sport_booking/reservations/test_portal_requirements.py#L41) | [REQ-07](../requirements/public-catalog.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_registration_creates_only_customer_and_authenticates`](../../sport_booking/reservations/test_portal_requirements.py#L59) | [REQ-08](../requirements/customer-registration.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_staff_personal_list_still_contains_only_own_reservations`](../../sport_booking/reservations/test_portal_requirements.py#L170) | [REQ-10](../requirements/my-reservations.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_staff_queue_displays_empty_state`](../../sport_booking/reservations/test_portal_requirements.py#L220) | [REQ-11](../requirements/staff-approval-queue.md) |
| [test_portal_requirements.py](../../sport_booking/reservations/test_portal_requirements.py) | [`PortalRequirementTests.test_staff_queue_shows_only_pending_before_start_without_mutation`](../../sport_booking/reservations/test_portal_requirements.py#L197) | [REQ-11](../requirements/staff-approval-queue.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`HourBlockRuleTests.test_daylight_saving_days_have_real_hour_blocks`](../../sport_booking/reservations/test_schedule.py#L16) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`HourBlockRuleTests.test_two_hour_limit_uses_elapsed_time_across_dst`](../../sport_booking/reservations/test_schedule.py#L29) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`HourBlockRuleTests.test_unavailable_resource_disables_all_blocks`](../../sport_booking/reservations/test_schedule.py#L42) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`HourBlockRuleTests.test_week_table_represents_dst_gap_and_repeated_hour`](../../sport_booking/reservations/test_schedule.py#L49) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`ScheduleTests.test_approval_required_resource_creates_pending_from_blocks`](../../sport_booking/reservations/test_schedule.py#L143) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`ScheduleTests.test_availability_from_blocks_is_read_only`](../../sport_booking/reservations/test_schedule.py#L179) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`ScheduleTests.test_confirmed_partial_overlap_blocks_whole_hour_and_edges_remain_free`](../../sport_booking/reservations/test_schedule.py#L115) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`ScheduleTests.test_grid_renders_hour_blocks_and_manual_option`](../../sport_booking/reservations/test_schedule.py#L86) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`ScheduleTests.test_guest_cannot_submit_grid_booking`](../../sport_booking/reservations/test_schedule.py#L194) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`ScheduleTests.test_invalid_resource_and_day_do_not_create_reservation`](../../sport_booking/reservations/test_schedule.py#L162) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`ScheduleTests.test_manual_input_keeps_two_hour_server_limit`](../../sport_booking/reservations/test_schedule.py#L183) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`ScheduleTests.test_one_or_two_blocks_create_exact_one_or_two_hour_reservation`](../../sport_booking/reservations/test_schedule.py#L95) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`ScheduleTests.test_past_and_beyond_thirty_days_are_disabled`](../../sport_booking/reservations/test_schedule.py#L171) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`ScheduleTests.test_pending_other_resource_and_cancelled_do_not_block`](../../sport_booking/reservations/test_schedule.py#L132) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`ScheduleTests.test_slot_interval_is_derived_on_server_not_client_values`](../../sport_booking/reservations/test_schedule.py#L199) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`ScheduleTests.test_stale_schedule_does_not_bypass_atomic_conflict_check`](../../sport_booking/reservations/test_schedule.py#L151) | [REQ-12](../requirements/hourly-schedule.md) |
| [test_schedule.py](../../sport_booking/reservations/test_schedule.py) | [`ScheduleTests.test_three_nonadjacent_duplicate_and_unknown_blocks_are_rejected`](../../sport_booking/reservations/test_schedule.py#L107) | [REQ-12](../requirements/hourly-schedule.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_approval_request_does_not_block_until_staff_approves`](../../sport_booking/reservations/tests.py#L181) | [REQ-02](../requirements/check-availability.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_authentication_ownership_and_unknown_resource`](../../sport_booking/reservations/tests.py#L222) | [REQ-01](../requirements/create-reservation.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_automatic_creation_rejects_existing_pending_requests`](../../sport_booking/reservations/tests.py#L207) | [REQ-03](../requirements/confirm-reservation.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_availability_checks_confirmed_only_and_half_open_edges`](../../sport_booking/reservations/tests.py#L170) | [REQ-02](../requirements/check-availability.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_cancel_confirmed_releases_resource_and_rejects_repeat`](../../sport_booking/reservations/tests.py#L263) | [REQ-05](../requirements/cancel-reservation.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_confirm_endpoint_removed_and_terminal_states_cannot_reopen`](../../sport_booking/reservations/tests.py#L339) | [REQ-03](../requirements/confirm-reservation.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_confirmation_rejects_only_overlapping_pending_same_resource`](../../sport_booking/reservations/tests.py#L192) | [REQ-06](../requirements/approve-reservation.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_create_pending_checks_conflicts_and_inactive_resource`](../../sport_booking/reservations/tests.py#L156) | [REQ-01](../requirements/create-reservation.md), [REQ-03](../requirements/confirm-reservation.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_create_succeeds_and_rejects_invalid_interval`](../../sport_booking/reservations/tests.py#L147) | [REQ-01](../requirements/create-reservation.md), [REQ-03](../requirements/confirm-reservation.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_delayed_approval_succeeds_after_24_hours_before_start`](../../sport_booking/reservations/tests.py#L280) | [REQ-06](../requirements/approve-reservation.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_exact_time_limits_and_exceeded_limits`](../../sport_booking/reservations/tests.py#L239) | [REQ-01](../requirements/create-reservation.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_expiry_exact_deadline_on_approve_cancel_and_command`](../../sport_booking/reservations/tests.py#L305) | [REQ-05](../requirements/cancel-reservation.md), [REQ-06](../requirements/approve-reservation.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_inactive_resource_and_invalid_availability`](../../sport_booking/reservations/tests.py#L253) | [REQ-02](../requirements/check-availability.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_invalid_approval_decision_is_rejected_without_state_change`](../../sport_booking/reservations/tests.py#L332) | [REQ-06](../requirements/approve-reservation.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_invalid_calendar_date_returns_error_without_creating`](../../sport_booking/reservations/tests.py#L234) | [REQ-01](../requirements/create-reservation.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_owner_can_cancel_pending_approval_but_not_after_start`](../../sport_booking/reservations/tests.py#L269) | [REQ-05](../requirements/cancel-reservation.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_pending_request_remains_actionable_after_24_hours_until_start`](../../sport_booking/reservations/tests.py#L287) | [REQ-05](../requirements/cancel-reservation.md), [REQ-06](../requirements/approve-reservation.md) |
| [tests.py](../../sport_booking/reservations/tests.py) | [`ReservationApiTests.test_staff_can_reject_but_non_staff_cannot_decide`](../../sport_booking/reservations/tests.py#L216) | [REQ-06](../requirements/approve-reservation.md) |
| [web_views.py](../../sport_booking/reservations/web_views.py) | [`BookingForm.clean`](../../sport_booking/reservations/web_views.py#L115) | [REQ-12](../requirements/hourly-schedule.md) |
| [web_views.py](../../sport_booking/reservations/web_views.py) | [`OperatingHoursForm`](../../sport_booking/reservations/web_views.py#L27) | [REQ-13](../requirements/operating-hours.md) |
| [web_views.py](../../sport_booking/reservations/web_views.py) | [`PortalLoginView`](../../sport_booking/reservations/web_views.py#L292) | [REQ-09](../requirements/login-logout.md) |
| [web_views.py](../../sport_booking/reservations/web_views.py) | [`PortalLogoutView`](../../sport_booking/reservations/web_views.py#L297) | [REQ-09](../requirements/login-logout.md) |
| [web_views.py](../../sport_booking/reservations/web_views.py) | [`RegistrationForm`](../../sport_booking/reservations/web_views.py#L21) | [REQ-08](../requirements/customer-registration.md) |
| [web_views.py](../../sport_booking/reservations/web_views.py) | [`ScheduleFilterForm`](../../sport_booking/reservations/web_views.py#L41) | [REQ-12](../requirements/hourly-schedule.md) |
| [web_views.py](../../sport_booking/reservations/web_views.py) | [`home`](../../sport_booking/reservations/web_views.py#L138) | [REQ-07](../requirements/public-catalog.md), [REQ-10](../requirements/my-reservations.md), [REQ-11](../requirements/staff-approval-queue.md), [REQ-12](../requirements/hourly-schedule.md) |
| [web_views.py](../../sport_booking/reservations/web_views.py) | [`register`](../../sport_booking/reservations/web_views.py#L280) | [REQ-08](../requirements/customer-registration.md) |
| [web_views.py](../../sport_booking/reservations/web_views.py) | [`update_operating_hours`](../../sport_booking/reservations/web_views.py#L320) | [REQ-13](../requirements/operating-hours.md) |
