from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Question, Answer

# تعریف Inline برای مدل Question
class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    readonly_fields = ('question_text', 'question_type', 'title', 'date_asked')
    can_delete = False
    fields = ('question_text', 'question_type', 'title', 'date_asked')

# تعریف Admin برای مدل Question
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'question_text', 'question_type', 'title', 'date_asked')
    search_fields = ('question_text', 'title', 'keywords')
    list_filter = ('question_type', 'date_asked')
    date_hierarchy = 'date_asked'
    ordering = ('-date_asked',)

# تعریف Admin برای مدل Answer
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'answer_text', 'date_answered')
    search_fields = ('answer_text',)
    list_filter = ('date_answered',)
    date_hierarchy = 'date_answered'
    ordering = ('-date_answered',)

# سفارشی‌سازی مدل User
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'last_login')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    ordering = ('username',)

    # اضافه کردن Inline های جدید
    inlines = [QuestionInline]

# ثبت مدل‌ها در پنل مدیریت
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer, AnswerAdmin)
