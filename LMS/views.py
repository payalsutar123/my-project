from time import time
from django.contrib import messages
from django.shortcuts import render,redirect,get_object_or_404,Http404
from app.models import Categories,Course,Level,Video,UserCourse,PaymentList,Rating,Wishlist,UserProfile
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.db.models import Sum,Avg,Count,Max,Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect,reverse
from .forms import RatingForm
import math
from .settings import *
import razorpay
from time import time
from django.core.paginator import Paginator

client = razorpay.Client(auth =(RAZORPAY_API_KEY,RAZORPAY_API_SECRET_KEY))


def BASE(request):
    return render(request,'base.html')

def HOME(request):
    category = Categories.objects.all().order_by('id')[0:5]
    course = Course.objects.filter(status='PUBLISH').order_by('id')

    # Calculate the rating with the maximum number of votes and total reviews for each course
    for c in course:
        ratings = Rating.objects.filter(course=c)
        max_rating = ratings.values('rating').annotate(count=Count('rating')).order_by('-count').first()
        c.max_rating = max_rating['rating'] if max_rating else 0
        c.total_reviews = ratings.count()
        
        time_duration = Video.objects.filter(course=c).aggregate(sum_duration=Sum('time_duration'))
        c.time_duration = time_duration['sum_duration'] if time_duration['sum_duration'] else 0

    # Define the stars_range variable
    stars_range = range(5)  # Assuming a maximum of 5 stars

    context = {
        'category': category,
        'course': course,
        'stars_range': stars_range,
    }
    return render(request, 'Main/home.html', context)

def SINGLE_COURSE(request):
    category = Categories.get_all_category(Categories)
    level = Level.objects.all()
    course = Course.objects.all()
    FreeCourse_count = Course.objects.filter(price=0).count()
    PaidCourse_count = Course.objects.filter(price__gte=1).count()
    
    sort_option = request.GET.get('sort')  # Get the sort option from the query parameters
    
    if sort_option == 'popular':
        course = Course.objects.annotate(num_votes=Count('ratings')).order_by('-num_votes')
    elif sort_option == 'top_rated':
        course = Course.objects.annotate(avg_rating=Avg('ratings__rating')).order_by('-avg_rating')
    
    paginator = Paginator(course, 6)
    page_number = request.GET.get('page')
    ServiceDataFinal = paginator.get_page(page_number)
    totalpage = ServiceDataFinal.paginator.num_pages
    
    # Calculate the total reviews and find the rating with the maximum votes for each course
    for c in ServiceDataFinal:
        ratings = Rating.objects.filter(course=c)
        c.total_reviews = ratings.count()
        max_rating = ratings.values('rating').annotate(count=Count('rating')).order_by('-count').first()
        c.max_rating = max_rating['rating'] if max_rating else 0
        time_duration = Video.objects.filter(course=c).aggregate(sum_duration=Sum('time_duration'))
        c.time_duration = time_duration['sum_duration'] if time_duration['sum_duration'] else 0
        
        # Count ratings for each star level
        c.one_star_count = ratings.filter(rating=1).count()
        c.two_star_count = ratings.filter(rating=2).count()
        c.three_star_count = ratings.filter(rating=3).count()
        c.four_star_count = ratings.filter(rating=4).count()
        c.five_star_count = ratings.filter(rating=5).count()

    stars_range = range(5)
    
    # Generate the list of page numbers for pagination
    page_numbers = [n + 1 for n in range(totalpage)]

    context = {
        'category': category,
        'level': level,
        'FreeCourse_count': FreeCourse_count,
        'PaidCourse_count': PaidCourse_count,
        'course': ServiceDataFinal,
        'lastpage': totalpage,
        'totalPagelist': page_numbers,
        'stars_range': stars_range,
        'sort_option': sort_option,
    }
    return render(request, 'Main/single_course.html', context)

def filter_data(request):
    category = request.GET.getlist('category[]')
    level = request.GET.getlist('level[]')
    price = request.GET.getlist('price[]')
    rating = request.GET.getlist('rating[]')

    course = Course.objects.all()

    # Apply filters
    if price == ['PriceFree']:
        course = course.filter(price=0)
    elif price == ['PricePaid']:
        course = course.filter(price__gte=1)

    if category:
        course = course.filter(category__id__in=category)

    if level:
        course = course.filter(level__id__in=level)

    if rating:
        max_rating = int(rating[0][-1])
        if max_rating == 5:
            course = course.annotate(max_rating_count=Count('ratings', filter=Q(ratings__rating=5))).filter(max_rating_count__gt=0)
        else:
            course = course.annotate(max_rating_count=Count('ratings', filter=Q(ratings__rating=max_rating))).filter(max_rating_count__gt=0)

    # Calculate the rating with the maximum number of votes and total reviews for each course
    for c in course:
        ratings = Rating.objects.filter(course=c)
        max_rating = ratings.values('rating').annotate(count=Count('rating')).order_by('-count').first()
        c.max_rating = max_rating['rating'] if max_rating else 0
        c.total_reviews = ratings.count()

        time_duration = Video.objects.filter(course=c).aggregate(sum_duration=Sum('time_duration'))
        c.time_duration = time_duration['sum_duration'] if time_duration['sum_duration'] else 0


        c.one_star_count = ratings.filter(rating=1).count()
        c.two_star_count = ratings.filter(rating=2).count()
        c.three_star_count = ratings.filter(rating=3).count()
        c.four_star_count = ratings.filter(rating=4).count()
        c.five_star_count = ratings.filter(rating=5).count()

    stars_range = range(5)
        # Define the stars_range variable for the maximum rating

    # Pagination
    paginator = Paginator(course, 5)  # Adjust the number of items per page as needed
    page_number = request.GET.get('page')
    course_page = paginator.get_page(page_number)

    # Render the HTML for the filtered courses
    context = {
        'course': course_page,
        'stars_range': stars_range,
    }
    filtered_courses_html = render_to_string('ajax/course.html', context)

    # Return the filtered courses HTML and total number of pages
    return JsonResponse({
        'data': filtered_courses_html,
        'total_pages': paginator.num_pages,
    })







def CONTACT_US(request):
    category=Categories.get_all_category(Categories)

    context = {
        'category':category
    }
    return render(request,'Main/contact_us.html',context)

def ABOUT_US(request):
    category=Categories.get_all_category(Categories)

    context = {
        'category':category
    }
    return render(request,'Main/about_us.html',context)

def SEARCH_COURSE(request):
    category=Categories.get_all_category(Categories)

    query=request.GET['query']
    course=Course.objects.filter(title__icontains =query)
    print(course)

    context = {
        'course':course,
        'category':category
    }
    return render(request,'search/search.html',context)

@login_required
def COURSE_DETAILS(request, slug):
    user_profile = None
    if hasattr(request.user, 'userprofile'):
        user_profile = request.user.userprofile

    category = Categories.get_all_category(Categories)
    time_duration = Video.objects.filter(course__slug=slug).aggregate(sum=Sum('time_duration'))

    course_id = Course.objects.get(slug=slug)
    try:
        check_enroll = UserCourse.objects.filter(user=request.user, course=course_id).first()


    except UserCourse.DoesNotExist:
        check_enroll = None

    course = Course.objects.filter(slug=slug)
    if course.exists():
        course = course.first()
    else:
        return redirect('http://127.0.0.1:8000/404')

    # Get the ratings for the course
    ratings = Rating.objects.filter(course=course)

    # Get the average rating value for the course
    rating_avg = Rating.objects.filter(course=course).aggregate(Avg('rating'))['rating__avg']
    rounded_avg = math.ceil(rating_avg) if rating_avg else 0
    stars_range = range(rounded_avg)

    # Get the reviews for the course
    reviews = Rating.objects.filter(course=course)

    # Count the ratings for each star rating
    one_star_count = ratings.filter(rating=1).count()
    two_star_count = ratings.filter(rating=2).count()
    three_star_count = ratings.filter(rating=3).count()
    four_star_count = ratings.filter(rating=4).count()
    five_star_count = ratings.filter(rating=5).count()

    # Find the maximum count of ratings
    max_count = max(one_star_count, two_star_count, three_star_count, four_star_count, five_star_count)

    # Determine the rating with the maximum count
    if max_count == one_star_count:
        max_rating = 1
    elif max_count == two_star_count:
        max_rating = 2
    elif max_count == three_star_count:
        max_rating = 3
    elif max_count == four_star_count:
        max_rating = 4
    else:
        max_rating = 5

    if max_count == 0:
        max_rating = 0    

    context = {
        'course': course,
        'category': category,
        'time_duration': time_duration,
        'check_enroll': check_enroll,
        'ratings': ratings,
        'reviews': reviews,
        'stars_range': range(5),
        'one_star_count': one_star_count,
        'two_star_count': two_star_count,
        'three_star_count': three_star_count,
        'four_star_count': four_star_count,
        'five_star_count': five_star_count,
        'max_rating': max_rating,
        'user_profile': user_profile,
    }

    return render(request, 'course/course_details.html', context)





def PAGE_NOT_FOUND(request):
    category=Categories.get_all_category(Categories)
    context = {
        'category':category
    }
    return render(request,'error/404.html',context)

def CHECKOUT(request,slug):
    course = Course.objects.get(slug=slug)
    action = request.GET.get('action')
    order = None
    
    if course.price == 0:
        course=UserCourse(
            user = request.user,
            course = course,
        )
        course.save()
        messages.success(request, 'Course are successfully Enrolled')
        return redirect('my-course')
    
    elif action == 'create_payment':
        if request.method == "POST":
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            country = request.POST.get('country')
            address_1 = request.POST.get('address_1')
            address_2 = request.POST.get('address_2')
            city = request.POST.get('city')
            state= request.POST.get('state')
            postcode = request.POST.get('postcode')
            phone = request.POST.get('phone')
            email =request.POST.get('email')
            order_comments = request.POST.get('order_comments')

            amount_cal = course.price - (course.price * course.discount/100)
            amount = int(amount_cal) * 100
            currency = "INR"
            notes = {
                "name":f'{first_name} {last_name}',
                "country": country,
                "address":f'{address_1} {address_2}',
                "city": city,
                "state": state,
                "postcode": postcode,
                "phone": phone,
                "email": email,
                "order_comments":order_comments,


            }
            receipt = f"Skola-{int(time())}"
            order = client.order.create(
                {
                    'receipt':receipt,
                    'notes':notes,
                    'amount':amount,
                    'currency':currency,
                }
            )
            payment = PaymentList(
                course = course,
                user = request.user,
                order_id = order.get('id')
            )
            payment.save()       
            
    context = {
        'course': course,
        'order': order

    }
    return render(request,'checkout/checkout.html',context)

def MY_COURSE(request):
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        try:
            course = UserCourse.objects.get(user=request.user, id=course_id)
            messages.warning(request, 'Course is already in your course list.')
        except UserCourse.DoesNotExist:
            # Course not in user's course list, you can add it to the list here if needed.
            pass

    course = UserCourse.objects.filter(user=request.user).order_by('id').distinct()
    context = {
        'course': course,
    }
    return render(request, 'course/my_course.html', context)



def WATCH_COURSE(request,slug):
    course = Course.objects.filter(slug = slug)
    lecture = request.GET.get('lecture')

    try:
        video = Video.objects.get(id = lecture)
    except Video.DoesNotExist:
        video = Video.objects.filter(id = lecture)

    if course.exists():
        course = course.first()
    else:
        return redirect('404')

    context = {
        'course': course,
        'video':video,
        
    }    
    return render(request,'course/watch-course.html',context)

@csrf_exempt
def VERIFY_PAYMENT(request):
    if request.method == "POST":
        data = request.POST
        print(data)
        try:
            client.utility.verify_payment_signature(data)
            razorpay_order_id = data['razorpay_order_id']
            razorpay_payment_id = data['razorpay_payment_id']

            payment = PaymentList.objects.get(order_id = razorpay_order_id)
            payment.payment_id = razorpay_payment_id
            payment.status = True

            usercourse = UserCourse(
                user = payment.user,
                course = payment.course,
            )
            usercourse.save()
            payment.user_course = usercourse
            payment.save()
            

            context = {
                'data' : data,
                'payment':payment
            }
            return render(request,'verify_payment/success.html', context)
        except:
            return render(request,'verify_payment/fail.html')
    return None


def AUTHORPRO(request):
    return render(request,'course/author_profile.html')



def submit_review(request, course_slug):
    if request.method == 'POST':
        form = RatingForm(request.POST, request.FILES)
        if form.is_valid():
            username = request.POST.get('username')
            rating = form.cleaned_data['rating']
            text = form.cleaned_data['text']

            # Save the review to the database
            course = Course.objects.get(slug=course_slug)
            user = request.user
            review = Rating(course=course, user=user,rating=rating, text=text)
            review.save()

            # Redirect to the course details page after review submission
            return redirect('course_details', slug=course_slug)
    else:
        form = RatingForm()

    context = {
        'form': form,
    }

    return render(request, 'submit_review.html', context)


def WishListView(request):
    category = Categories.get_all_category(Categories)
    courses = Course.objects.all()
    wish_items = Wishlist.objects.filter(user=request.user)

    for item in wish_items:
        ratings = Rating.objects.filter(course=item.course)
        max_rating = ratings.values('rating').annotate(count=Count('rating')).order_by('-count').first()
        item.course.max_rating = max_rating['rating'] if max_rating else 0
        item.course.total_reviews = ratings.count()

        time_duration = Video.objects.filter(course=item.course).aggregate(sum=Sum('time_duration'))
        item.course.time_duration = time_duration['sum'] if time_duration['sum'] else 0

    stars_range = range(5)  # Assuming a maximum of 5 stars

    paginator = Paginator(wish_items, 3)  # Specify the number of items per page
    page_number = request.GET.get('page')
    wish_items_paginated = paginator.get_page(page_number)

    context = {
        'wish_items': wish_items_paginated,
        'category': category,
        'courses': courses,
        'stars_range': stars_range,
    }

    return render(request, 'course/wishlist.html', context)
    

@login_required
def add_to_wishlist(request, course_slug):
    if request.method == 'POST':
        try:
            course = Course.objects.get(slug=course_slug)
            wishlist_item = Wishlist(user=request.user, course=course)
            wishlist_item.save()
            # Add a success message or any additional logic

            return redirect('wishlist')  # Redirect to the wishlist page
        except Course.DoesNotExist:
            raise Http404("Course does not exist.")

    return render(request, 'Main/home.html')



def remove_from_wishlist(request, course_slug):
    if request.method == 'POST':
        try:
            course = Course.objects.get(slug=course_slug)
            Wishlist.objects.filter(user=request.user, course=course).delete()
            # Add a success message or any additional logic

            return redirect('wishlist')  # Redirect to the wishlist page
        except Course.DoesNotExist:
            raise Http404("Course does not exist.")

    return render(request, 'Main/home.html')


def AUTHORPRO(request, course_slug):
    # Retrieve the course based on the provided slug
    course = get_object_or_404(Course, slug=course_slug)

    # Retrieve the author associated with the course
    author = course.author

    # Retrieve the courses associated with the author
    courses = Course.objects.filter(author=author)

   
    for course_item in courses:
        ratings = Rating.objects.filter(course=course_item)
        max_rating = ratings.values('rating').annotate(count=Count('rating')).order_by('-count').first()
        course_item.max_rating = max_rating['rating'] if max_rating else 0
        course_item.total_reviews = ratings.count()
        
        time_duration = Video.objects.filter(course=course_item).aggregate(sum_duration=Sum('time_duration'))
        course_item.time_duration = time_duration['sum_duration'] if time_duration['sum_duration'] else 0

    # Define the stars_range variable
    stars_range = range(5)  # Assuming a maximum of 5 stars


    context = {
        'author': author,
        'course': course,
        'course_items': courses,  # Rename the variable to avoid conflict
        'stars_range': stars_range,    
        }

    return render(request, 'course/author_profile.html', context)




