from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import logout
from django.contrib import messages
from datetime import datetime
from .models import CarMake, CarModel
from .restapis import get_request, analyze_review_sentiments, post_review

from django.http import JsonResponse
from django.contrib.auth import login, authenticate
import logging
import json
from django.views.decorators.csrf import csrf_exempt
from .populate import initiate


# Get an instance of a logger
logger = logging.getLogger(__name__)

# Create a `login_request` view to handle sign in request
@csrf_exempt
def login_user(request):
    # Get username and password from request.POST dictionary
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    # Try to check if provide credential can be authenticated
    user = authenticate(username=username, password=password)
    data = {"userName": username}
    if user is not None:
        # If user is valid, call login method to login current user
        login(request, user)
        data = {"userName": username, "status": "Authenticated"}
    return JsonResponse(data)

# Create a `logout_request` view to handle sign out request
@csrf_exempt
def logout_request(request):
    logout(request)
    data = {"userName":""}
    return JsonResponse(data)

# Create a `registration` view to handle sign up request
@csrf_exempt
def registration(request):
    context = {}
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    first_name = data['firstName']
    last_name = data['lastName']
    email = data['email']
    username_exist = False
    email_exist = False
    try:
        # Check if user already exists
        User.objects.get(username=username)
        username_exist = True
    except:
        # If not, simply log this is a new user
        logger.debug("{} is new user".format(username))
    # If it is a new user
    if not username_exist:
        # Create user in auth_user table
        user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,password=password, email=email)
        # Login the user and redirect to list page
        login(request, user)
        data = {"userName":username,"status":"Authenticated"}
        return JsonResponse(data)
    else :
        data = {"userName":username,"error":"Already Registered"}
        return JsonResponse(data)

# Function to retrieve cars
def get_cars(request):
    # Count the number of CarMake objects in the database
    count = CarMake.objects.filter().count()
    
    # Print the count (for debugging purposes)
    print(count)
    
    # If there are no CarMake objects in the database, initiate some data
    if count == 0:
        initiate()
    
    # Retrieve all CarModel objects along with their related CarMake objects
    car_models = CarModel.objects.select_related('car_make')
    
    # Initialize an empty list to store car data
    cars = []
    
    # Iterate over each car model
    for car_model in car_models:
        # Append car model and car make names to the list
        cars.append({"CarModel": car_model.name, "CarMake": car_model.car_make.name})
    
    # Return a JSON response containing car data
    return JsonResponse({"CarModels": cars})

#Update the `get_dealerships` view to render the index page with
def get_dealerships(request, state="All"):
    if(state == "All"):
        endpoint = "/fetchDealers"
    else:
        endpoint = "/fetchDealers/"+state
    dealerships = get_request(endpoint)
    return JsonResponse({"status":200,"dealers":dealerships})

# Function to retrieve dealer details
def get_dealer_details(request, dealer_id):
    # Check if dealer_id is provided
    if dealer_id:
        # Construct the endpoint for fetching dealer details
        endpoint = "/fetchDealer/" + str(dealer_id)
        
        # Make a GET request to fetch dealership details
        dealership = get_request(endpoint)
        
        # Return JSON response with status 200 and dealer details
        return JsonResponse({"status": 200, "dealer": dealership})
    else:
        # Return JSON response with status 400 and error message for bad request
        return JsonResponse({"status": 400, "message": "Bad Request"})
    
# Function to retrieve dealer reviews
def get_dealer_reviews(request, dealer_id):
    # Check if dealer_id is provided
    if dealer_id:
        # Construct the endpoint for fetching dealer reviews
        endpoint = "/fetchReviews/dealer/" + str(dealer_id)
        
        # Make a GET request to fetch reviews
        reviews = get_request(endpoint)
        
        # Iterate over each review and analyze its sentiment
        for review_detail in reviews:
            # Analyze sentiment of the review
            response = analyze_review_sentiments(review_detail['review'])
            
            # Print the sentiment response (for debugging purposes)
            print(response)
            
            # Add sentiment information to the review detail
            review_detail['sentiment'] = response['sentiment']
        
        # Return JSON response with status 200 and reviews
        return JsonResponse({"status": 200, "reviews": reviews})
    else:
        # Return JSON response with status 400 and error message for bad request
        return JsonResponse({"status": 400, "message": "Bad Request"})

# Function to add a review
def add_review(request):
    # Check if the user is authenticated
    if not request.user.is_anonymous:
        # Load JSON data from the request body
        data = json.loads(request.body)
        
        try:
            # Try to post the review using the post_review function
            response = post_review(data)
            
            # If successful, return a JSON response with status 200
            return JsonResponse({"status": 200})
        except Exception as e:
            # If an error occurs during posting the review, return a JSON response with status 401 and error message
            return JsonResponse({"status": 401, "message": "Error in posting review"})
    else:
        # If the user is anonymous, return a JSON response with status 403 and error message
        return JsonResponse({"status": 403, "message": "Unauthorized"})
