from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Sum
from django.core.cache import cache
from django.utils import timezone
from .models import Department, Posters, Student, Category, Result, Schedule, Image

class CustomAdminSite(admin.AdminSite):
    site_header = 'KABYKA PSMO Admin Portal'
    site_title = 'KABYKA PSMO Admin'
    index_title = 'Fine Arts Festival Management'
    
    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        # Add custom styling to the admin interface
        app_list.append({
            'name': 'Quick Links',
            'app_label': 'quick_links',
            'models': [{
                'name': 'Today\'s Events',
                'object_name': 'today_events',
                'admin_url': '/admin/events/schedule/?date__day=' + timezone.now().strftime('%d'),
                'view_only': True,
            }, {
                'name': 'Latest Results',
                'object_name': 'latest_results',
                'admin_url': '/admin/events/result/',
                'view_only': True,
            }],
        })
        return app_list

admin_site = CustomAdminSite(name='custom_admin')

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'total_points', 'student_count', 'participation_count')
    search_fields = ('name', 'code')
    ordering = ('-total_points', 'name')
    
    def student_count(self, obj):
        return Student.objects.filter(department=obj).count()
    student_count.short_description = 'Students'
    
    def participation_count(self, obj):
        cache_key = f'department_{obj.id}_participation_count'
        count = cache.get(cache_key)
        if count is None:
            count = Result.objects.filter(
                first_place__department=obj
            ).count() + Result.objects.filter(
                second_place__department=obj
            ).count() + Result.objects.filter(
                third_place__department=obj
            ).count()
            cache.set(cache_key, count, 3600)  # Cache for 1 hour
        return count
    participation_count.short_description = 'Participations'

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'registration_number', 'phone', 'event_count')
    list_filter = ('department',)
    search_fields = ('name', 'registration_number', 'phone')
    ordering = ('name',)
    
    def event_count(self, obj):
        return Result.objects.filter(
            first_place=obj
        ).count() + Result.objects.filter(
            second_place=obj
        ).count() + Result.objects.filter(
            third_place=obj
        ).count()
    event_count.short_description = 'Events Participated'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'max_participants', 'event_count')
    list_filter = ('group',)
    search_fields = ('name',)
    
    def event_count(self, obj):
        return Schedule.objects.filter(category=obj).count()
    event_count.short_description = 'Total Events'

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('program', 'category', 'date', 'time', 'venue', 'status', 'has_results')
    list_filter = ('date', 'status', 'category__group')
    search_fields = ('program', 'venue')
    date_hierarchy = 'date'
    list_editable = ('status',)
    
    def has_results(self, obj):
        has_result = Result.objects.filter(program=obj.program).exists()
        return format_html(
            '<span class="{}"><i class="fas fa-{}"></i></span>',
            'text-green-600' if has_result else 'text-red-600',
            'check' if has_result else 'times'
        )
    has_results.short_description = 'Results Added'

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'display_image', 'uploaded_at')
    search_fields = ('title',)
    readonly_fields = ('uploaded_at',)

    def display_image(self, obj):
        return format_html(
            '<img src="{}" width="50" height="50" style="border-radius: 5px; object-fit: cover;" />',
            obj.image.url
        )
    display_image.short_description = 'Preview'

@admin.register(Posters)
class PostersAdmin(admin.ModelAdmin):
    list_display = ('title', 'display_poster', 'created_at')
    search_fields = ('title',)
    readonly_fields = ('created_at',)

    def display_poster(self, obj):
        return format_html(
            '<img src="{}" width="100" height="100" style="border-radius: 8px; object-fit: cover;" />',
            obj.image.url
        )
    display_poster.short_description = 'Poster Preview'

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('program', 'category', 'group', 'display_winners', 'created_at')
    list_filter = ('category', 'group', 'created_at')
    search_fields = ('program', 'first_place__name', 'second_place__name', 'third_place__name')
    filter_horizontal = ('first_place', 'second_place', 'third_place')
    readonly_fields = ('created_at',)
    
    def display_winners(self, obj):
        winners = []
        if obj.first_place.exists():
            winners.append(format_html(
                '<span class="text-gold">🥇 {}</span>',
                ', '.join(str(s) for s in obj.first_place.all())
            ))
        if obj.second_place.exists():
            winners.append(format_html(
                '<span class="text-silver">🥈 {}</span>',
                ', '.join(str(s) for s in obj.second_place.all())
            ))
        if obj.third_place.exists():
            winners.append(format_html(
                '<span class="text-bronze">🥉 {}</span>',
                ', '.join(str(s) for s in obj.third_place.all())
            ))
        return format_html('<div style="min-width:300px">{}</div>', ' <br> '.join(winners))
    display_winners.short_description = 'Winners'

    class Media:
        css = {
            'all': ('admin/css/custom.css',)
        }
