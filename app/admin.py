from django.contrib import admin
from .models import *

class what_you_learn_TabularInline(admin.TabularInline):
    model = What_you_learn

class Requirements_TabularInline(admin.TabularInline):
    model = Requirements    

# class Video_TabularInline(admin.TabularInline):
#     model = Video    

class course_admin(admin.ModelAdmin):
    list_display=['title']

    inlines = (what_you_learn_TabularInline,Requirements_TabularInline)


    
class admin_Payment(admin.ModelAdmin):
    list_display = ['course','user','order_id','payment_id','date','status']
    exclude = ['user_course','payment_id','course','user','order_id','status']







# Register your models here.
admin.site.register(Categories)
admin.site.register(Author)
admin.site.register(Course,course_admin)
admin.site.register(Level)
admin.site.register(What_you_learn)
admin.site.register(Requirements)
admin.site.register(Lesson)
admin.site.register(Language)
admin.site.register(UserCourse)
admin.site.register(PaymentList,admin_Payment)
admin.site.register(Video)
admin.site.register(Rating)
admin.site.register(Wishlist)
admin.site.register(UserProfile)
