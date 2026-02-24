from django.contrib import admin
from .models import Issue, IssueComment, Project, ProjectComment


class IssueCommentInline(admin.TabularInline):
    model = IssueComment
    extra = 0
    readonly_fields = ['author', 'created_at']


class ProjectCommentInline(admin.TabularInline):
    model = ProjectComment
    extra = 0
    readonly_fields = ['author', 'created_at']


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ['title', 'priority', 'status', 'asset', 'requisition', 'reported_by', 'created_at']
    list_filter = ['priority', 'status', 'created_at']
    search_fields = ['title', 'description', 'asset__asset_id']
    readonly_fields = ['created_at', 'updated_at', 'reported_by']
    inlines = [IssueCommentInline]


@admin.register(IssueComment)
class IssueCommentAdmin(admin.ModelAdmin):
    list_display = ['issue', 'author', 'created_at']
    readonly_fields = ['created_at']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'priority', 'status', 'date', 'reported_by', 'created_at']
    list_filter = ['priority', 'status', 'created_at']
    search_fields = ['title', 'description', 'problem_statement']
    readonly_fields = ['created_at', 'updated_at', 'reported_by']
    filter_horizontal = ['categories', 'requisitions']
    inlines = [ProjectCommentInline]


@admin.register(ProjectComment)
class ProjectCommentAdmin(admin.ModelAdmin):
    list_display = ['project', 'author', 'created_at']
    readonly_fields = ['created_at']
