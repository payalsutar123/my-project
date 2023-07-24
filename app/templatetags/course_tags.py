from django import template
import math
register = template.Library()

@register.simple_tag
def discount_calculation(price,discount):
    if discount is None or discount is 0:
        return price
    sellprice = price
    sellprice = price - (price * discount/100)
    return math.floor(sellprice)
	

@register.simple_tag
def get_max_rating(max_ratings_dict, course_id):
    return max_ratings_dict.get(course_id, 0)