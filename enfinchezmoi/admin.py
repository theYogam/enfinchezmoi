from django.contrib import admin

from ikwen.core.models import Country
from enfinchezmoi.models import City, Hood, Post, Category, SubCategory, Owner


class CityAdmin(admin.ModelAdmin):
    list_display = ('name',)
    fields = ('name',)


class HoodAdmin(admin.ModelAdmin):
    list_display = ('name', 'city',)
    fields = ('name', 'city',)


class PostAdmin(admin.ModelAdmin):
    # prepopulated_fields = {"slug": ("",)}
    list_display = ('subcategory', 'owner', 'hood', 'surface', 'bedroom_count',
                    'bathroom_count', 'kitchen_count', 'saloon_count', 'room_count',
                    'cost', 'has_ac', 'has_parking', 'has_safeguard', 'has_cleaning_service', 'is_furnished', 'is_registered',
                    'description', 'is_active')
    fields = ('subcategory', 'owner', 'hood', 'surface', 'bedroom_count',
              'bathroom_count', 'kitchen_count', 'saloon_count', 'room_count',
              'cost', 'has_ac', 'has_parking', 'has_safeguard', 'has_cleaning_service', 'is_furnished', 'is_registered',
              'description', 'is_active')


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'language')
    fields = ('name', 'language')


class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    fields = ('name', 'category')


class OwnerAdmin(admin.ModelAdmin):
    list_display = ('member', 'phone', 'email')
    fields = ('member', 'phone', 'email')


class ReservationAdmin(admin.ModelAdmin):
    fields = ('start_on', 'end_on', 'status')
    readonly_fields = ('member', 'post')


class PaymentAdmin(admin.ModelAdmin):
    fields = ('member', 'reservation', 'status')


