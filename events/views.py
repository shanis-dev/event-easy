from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Posters, Result, Category, Department, Schedule, Student, Image

def home(request):
    images = Image.objects.all()
    return render(request, 'events/home.html', {'images': images})

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
