from django.shortcuts import render
from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from .serializers import *
from .models import *
from picamera import PiCamera 
from django.http import HttpResponse
import json 
import os
import time
from django.views.decorators.csrf import csrf_exempt
from django_filters import rest_framework as filters

camera = None
img_dir = '/var/www/html/scanner/imgs'
pgno = 0
started = False
currbookid = -1
currbook = None

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

class BookFilter(filters.FilterSet):
    partial_name = filters.CharFilter(name='name', lookup_expr='icontains')
    class Meta:
        model = Book
        fields = ['name', 'partial_name', 'category']
    
class BookViewSet(viewsets.ModelViewSet):
	queryset = Book.objects.all()
	serializer_class = BookSerializer
	filter_class = BookFilter
	
class TagViewSet(viewsets.ModelViewSet):
	queryset = Tag.objects.all()
	serializer_class = TagSerializer

class CategoryViewSet(viewsets.ModelViewSet):
	queryset = Category.objects.all()
	serializer_class = CategorySerializer
	filter_fields = ['name']

@csrf_exempt
def startBook(request):
	global started, currbookid, pgno, camera, currbook

	payload = json.loads(request.body.decode('utf-8'))
	bookid = payload['bookid']
	
	camera = PiCamera()
	
	if bookid is None:
		return HttpResponse('Invalid bookid')
	
	bookdir = img_dir + '/' + str(bookid)
	if os.path.exists(bookdir):
		return HttpResponse('Book already exists')
		
	os.makedirs(bookdir)
	pgno = 0
	started = True
	currbookid = bookid
	currbook = Book.objects.get(pk = currbookid)
	return HttpResponse('Started scanning book ' + currbook.name)
	
@csrf_exempt	
def stopBook(request):
	global started, currbookid, pgno, camera, currbook

	print(currbookid)
	payload = json.loads(request.body.decode('utf-8'))
	bookid = payload['bookid']
	if bookid != currbookid:
		return HttpResponse("Inconsistent bookids. Call /stopBook to flush previous session")

	started = False
	currbookid = -1
	camera.close()
	return HttpResponse('Stopped scanning book ' + currbook.name)


@csrf_exempt	
def scan(request):	
	global started, currbookid, pgno, camera, currbook

	payload = json.loads(request.body.decode('utf-8'))
	bookid = payload['bookid']
	
	if bookid < 1:
		return HttpResponse("Invalid bookid")
		
	if bookid != currbookid:
		return HttpResponse("Inconsistent bookids. Call /stopBook to flush previous session")
		
	bookdir = img_dir + '/' + str(bookid)
	scanfile = '%s/%d.jpg' % (bookdir, pgno)
	camera.capture(scanfile, format='jpeg')
	scan = Scan(page=pgno, loc=scanfile, book=currbook)
	scan.save()
	pgno += 1 
	return HttpResponse('{"loc": "imgs/%d/%d.jpg"}' % (bookid, pgno-1))
	
	
	
