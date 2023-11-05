from django.contrib import admin
from blog.models import BlogPost
from blog.models import Comment


admin.site.register(BlogPost)



@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'content', 'blog_post', 'created_at')
    list_select_related = ('blog_post', 'author')  # This optimizes the query




