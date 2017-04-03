from django.shortcuts import render
from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from .serializers import *
from .models import *
from picamera import PiCamera 
from django.http import HttpResponse
from django.http.response import HttpResponseBadRequest
import json 
import os
import time
from django.views.decorators.csrf import csrf_exempt
from django_filters import rest_framework as filters
import uuid

from channels.handler import AsgiHandler

camera = None
img_dir = '/var/www/html/imgs'
pgno = 0
started = False
currbookid = -1
currbook = None

TMPDIR = '/var/www/html/test'

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
def createBook(request):
	payload = json.loads(request.body.decode('utf-8'))
	print(payload)
	book_name = payload['name']

	count = Book.objects.filter(name = book_name).count()
	if count > 0:
		raise HttpResponseBadRequest('Book already exists')

	author_name = payload['author']
	author, _ = Author.objects.get_or_create(name = author_name )

	category_name = payload['category']
	category, _ = Category.objects.get_or_create(name = category_name)

	book = Book(name=book_name, author=author, category=category)
	book.save()
	return HttpResponse(json.dumps({'bookid': book.id}))

@csrf_exempt
def startBook(request):
	global started, currbookid, pgno, camera, currbook

	payload = json.loads(request.body.decode('utf-8'))
	bookid = payload['bookid']
	
	if not camera or camera.closed:
		camera = PiCamera()
	
	if bookid is None:
		return HttpResponseBadRequest('Invalid bookid')
	
	bookdir = img_dir + '/' + str(bookid)
	if not os.path.exists(bookdir):		
		os.makedirs(bookdir)
	
	lastscan = Scan.objects.filter(book__id = bookid).order_by('-page').first()	
	pgno = lastscan.page + 1 if lastscan else 1

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
		return HttpResponseBadRequest("Inconsistent bookids. Call /stopBook to flush previous session")

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

	imgloc = "../imgs/{bookid}/{scan_num}.jpg".format(bookid=bookid, scan_num=pgno-1)
	response = {'loc': imgloc, 'scanNum': pgno-1}
	return HttpResponse(json.dumps(response))

@csrf_exempt
def test(request):
	global TMPDIR, camera

	if camera is None or camera.closed:
		camera = PiCamera()

	randid = uuid.uuid4()
	scanfile = '%s/%s.jpg' % (TMPDIR, randid)
	camera.capture(scanfile, format='jpeg')
	return HttpResponse('{"loc": "../test/%s.jpg"}' % (randid))

def ws_message(message):

	print(message.content);
    # message.reply_channel.send({
    #     "text": message.content['text'],
    # })

