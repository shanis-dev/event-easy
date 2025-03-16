from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Posters, Result, Category, Department, Schedule, Student, Image
from django.db import models
from django.http import JsonResponse
import openai
from django.conf import settings
import json

def home(request):
    images = Image.objects.all()
    
    # Get departments data for graphs
    departments = Department.objects.all().order_by('-total_points')  # Order by points
    department_data = {
        'names': json.dumps([dept.name for dept in departments]),
        'points': json.dumps([dept.total_points for dept in departments])
    }
    
    # Get categories with their event counts and points
    categories = Category.objects.all()
    category_data = []
    for category in categories:
        # Get results for this category
        results = Result.objects.filter(category=category)
        event_count = results.count()
        
        # Calculate total points for this category
        total_points = 0
        for result in results:
            # Add points for first place (5 points each)
            total_points += result.first_place.count() * 5
            # Add points for second place (3 points each)
            total_points += result.second_place.count() * 3
            # Add points for third place (1 point each)
            total_points += result.third_place.count() * 1
        
        category_data.append({
            'name': category.name,
            'event_count': event_count,
            'max_points': total_points,
            'progress': int((event_count / (event_count + 1)) * 100) if event_count > 0 else 0
        })
    
    # Get counts for statistics
    event_count = Result.objects.count()
    department_count = Department.objects.count()
    participant_count = Student.objects.count()
    
    context = {
        'images': images,
        'categories': category_data,
        'department_names': department_data['names'],
        'department_points': department_data['points'],
        'stats': {
            'events': event_count,
            'departments': department_count,
            'participants': participant_count,
            'days': 7  # You might want to calculate this based on your schedule
        }
    }
    
    return render(request, 'events/home.html', context)

def schedule(request):
    posters = Schedule.objects.all()
    return render(request, 'events/schedule.html',{'posters': posters})

def news(request):
    news = Posters.objects.all()
    return render(request, 'events/news.html',{'news': news})

def results(request):
    results = Result.objects.all()
    return render(request, 'events/result_list.html', {'results': results})

def result_detail(request, result_id):
    result = get_object_or_404(Result, id=result_id)
    return render(request, 'events/result_detail.html', {'result': result})


from collections import defaultdict

def points_table(request):
    departments = Department.objects.all().order_by('-total_points')
    top_students_by_category = {}
    categories = Category.objects.all()

    for category in categories:
        # Get all the results for this category
        results = Result.objects.filter(category=category)

        # Dictionary to store aggregated points for each student
        student_points = defaultdict(int)

        for result in results:
            # Only include individual points if the result is not a group
            if not result.group:
                for student in result.first_place.all():
                    student_points[student.id] += 5
                for student in result.second_place.all():
                    student_points[student.id] += 3
                for student in result.third_place.all():
                    student_points[student.id] += 1

        # Convert the dictionary into a list of student objects with points
        students_with_points = [
            {'student': Student.objects.get(id=student_id), 'points_in_category': points}
            for student_id, points in student_points.items()
        ]

        # Sort students by points in this category (descending order)
        students_with_points = sorted(students_with_points, key=lambda x: x['points_in_category'], reverse=True)[:5]

        # Store the students with their points in the category
        top_students_by_category[category] = students_with_points

    return render(request, 'events/points.html', {
        'departments': departments,
        'top_students_by_category': top_students_by_category
    })

def chat_with_gpt(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            
            # Get relevant context from the database
            departments = Department.objects.all()
            categories = Category.objects.all()
            results = Result.objects.all()
            
            # Create context string
            context = "Current departments: " + ", ".join([f"{d.name} ({d.total_points} points)" for d in departments])
            context += "\nEvent categories: " + ", ".join([c.name for c in categories])
            context += "\nRecent results: " + ", ".join([f"{r.program}" for r in results[:5]])
            
            # Create system message with context
            system_message = f"""You are a helpful assistant for the College Arts Festival. 
            Here's the current context:
            {context}
            
            Please provide accurate information based on this context."""
            
            # Call OpenAI API
            openai.api_key = settings.OPENAI_API_KEY
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            # Extract the response
            bot_response = response.choices[0].message.content
            
            return JsonResponse({
                'response': bot_response,
                'status': 'success'
            })
            
        except Exception as e:
            return JsonResponse({
                'error': str(e),
                'status': 'error'
            }, status=500)
    
    return JsonResponse({'error': 'Only POST method is allowed', 'status': 'error'}, status=405)
