from django.contrib import admin
from django import forms
from user_profile_api.models import UserProfile, Room, Subject, Device, Career, CareerSubjectYear, SubjectSchedule
from django.utils import timezone
from user_profile_api.services import get_default_user_device_id, get_default_schedule_id
from .forms import UserProfileAdminForm

@admin.register(UserProfile)
class ManageUser(admin.ModelAdmin):
    form = UserProfileAdminForm
    list_display = ('user_device_id', 'dni', 'first_name', 'last_name', 'email', 'is_active', 'is_staff', 'profile_type', 'fileImage')
    ordering = ('user_device_id',)
    search_fields = ('user_device_id', 'dni', 'email', 'first_name', 'last_name')
    list_per_page = 50
    filter_vertical = ('subject',)
    exclude = ('planTemplateNo',)
    readonly_fields = ('date_created', 'last_updated', 'timeType')

    def save_model(self, request, obj, form, change):
        obj.last_updated = timezone.now()
        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        default_user_device_id = get_default_user_device_id()
        form.base_fields['user_device_id'].initial = default_user_device_id
        return form

@admin.register(Room)
class ManageRoom(admin.ModelAdmin):
    list_display = ('room', 'location')
    ordering = ('id',)
    search_fields = ('id',)
    list_per_page = 10

@admin.register(Career)
class ManageCareer(admin.ModelAdmin):
    list_display = ('name_career',)
    ordering = ('id',)
    search_fields = ('id', 'name_career')
    list_per_page = 10

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = '__all__'

@admin.register(Subject)
class ManageSubject(admin.ModelAdmin):
    list_display = ('subject',)
    ordering = ('id',)
    search_fields = ('id', 'subject')
    list_per_page = 10
    
@admin.register(CareerSubjectYear)
class ManageCareerSubjectYear(admin.ModelAdmin):
    list_display = ('career', 'subject', 'year')
    ordering = ('id',)
    search_fields = ('id', 'career', 'subject', 'year')
    list_per_page = 10

@admin.register(SubjectSchedule)
class ManageSubjectSchedule(admin.ModelAdmin):
    list_display = ('horario_id', 'device', 'career_subject_year', 'day', 'begin_time', 'end_time')
    ordering = ('horario_id',)
    search_fields = ('horario_id', 'career_subject_year')
    list_per_page = 10

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        default_horario_id = get_default_schedule_id()
        form.base_fields['horario_id'].initial = default_horario_id
        return form

@admin.register(Device)
class ManageDevice(admin.ModelAdmin):
    list_display = ('id', 'device', 'date_purchased', 'is_active', 'is_synchronized')
    ordering = ('id',)
    search_fields = ('id', 'device', 'date_purchased', 'user')
    list_per_page = 10
