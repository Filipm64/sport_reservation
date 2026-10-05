from django.contrib import admin

from .models import Reservation, Resource, Sport


@admin.register(Sport)
class SportAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'sport', 'location', 'opens_at', 'closes_at',
        'is_available', 'requires_approval',
    )
    list_filter = ('sport', 'is_available', 'requires_approval')
    search_fields = ('name', 'location', 'sport__name')
    list_select_related = ('sport',)
    autocomplete_fields = ('sport',)


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'resource', 'starts_at', 'ends_at', 'status', 'created_at')
    list_filter = ('status', 'resource__sport', 'starts_at')
    search_fields = ('user__username', 'user__email', 'resource__name')
    list_select_related = ('user', 'resource')
    autocomplete_fields = ('user', 'resource')
    readonly_fields = (
        'user', 'resource', 'starts_at', 'ends_at', 'status',
        'created_at', 'approval_requested_at',
    )
    date_hierarchy = 'starts_at'
    ordering = ('-starts_at',)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
