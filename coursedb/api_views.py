from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Course, CourseCategory
from .serializers import CourseSerializer, CourseCategorySerializer

@api_view(['GET'])
def category_list_api(request):
    categories = CourseCategory.objects.all()
    serializer = CourseCategorySerializer(categories, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def courses_by_category(request, category_id):
    courses = Course.objects.filter(category_id=category_id)
    serializer = CourseSerializer(courses, many=True)
    return Response(serializer.data)
@api_view(['GET'])
def course_list_api(request):
    courses = Course.objects.all()
    serializer = CourseSerializer(courses, many=True)
    return Response(serializer.data)