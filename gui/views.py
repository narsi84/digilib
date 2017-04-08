from django.shortcuts import render
from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from .serializers import *
from .models import *
from django.http import HttpResponse
from django.http.response import HttpResponseBadRequest
import json 
import os
import time
from django.views.decorators.csrf import csrf_exempt
from django_filters import rest_framework as filters
import uuid

from threading import Thread

from channels.handler import AsgiHandler

from .scanner import Scanner, ScanModes


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

def autoScanWorker():

class AutoScanner(Thread):
	def s

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
	scanner = Scanner.get_instance()

	payload = json.loads(request.body.decode('utf-8'))
	bookid = payload['bookid']
		
	if scanner.bookid is None:
		return HttpResponseBadRequest('Invalid bookid')
	
	bookdir = scanner.img_dir + '/' + str(bookid)
	if not os.path.exists(bookdir):		
		os.makedirs(bookdir)
	
	lastscan = Scan.objects.filter(book__id = bookid).order_by('-page').first()	
	pgno = lastscan.page + 1 if lastscan else 1

	scanner.started = True
	scanner.currbookid = bookid
	scanner.currbook = Book.objects.get(pk = currbookid)
	return HttpResponse('Started scanning book ' + scanner.currbook.name)
	
@csrf_exempt	
def stopBook(request):
	scanner = Scanner.get_instance()
	print(scanner.currbookid)
	payload = json.loads(request.body.decode('utf-8'))
	bookid = payload['bookid']
	if bookid != scanner.currbookid:
		return HttpResponseBadRequest("Inconsistent bookids. Call /stopBook to flush previous session")

	scanner.started = False
	scanner.currbookid = -1
	return HttpResponse('Stopped scanning book ' + scanner.currbook.name)


@csrf_exempt	
def scan(request):	
	scanner = Scanner.get_instance()
	scanner.mode = ScanModes.SINGLE_SCAN

	payload = json.loads(request.body.decode('utf-8'))
	bookid = payload['bookid']
	
	if bookid < 1:
		return HttpResponse("Invalid bookid")
		
	if bookid != scanner.currbookid:
		return HttpResponse("Inconsistent bookids. Call /stopBook to flush previous session")

	scanfile, pgno = scanner.scan()
	scan = Scan(page=pgno, loc=scanfile, book=scanner.currbook)
	scan.save()

	imgloc = os.path.join('../imgs/', scanfile)
	response = {'loc': imgloc, 'scanNum': pgno}
	return HttpResponse(json.dumps(response))


@csrf_exempt
def test(request):
	scanner = Scanner.get_instance()
	scanner.mode = ScanModes.TEST

	scanfile, _ = scanner.scan()
	return HttpResponse('{"loc": "../test/%s"}' % (scanfile))


@csrf_exempt
def auto_scan(request):
	scanner = Scanner.get_instance()

	payload = json.loads(request.body.decode('utf-8'))
	bookid = payload['bookid']
	state = payload['state']

	if state == True:
		scanner.set_mode(ScanModes.AUTO_SCAN)
	else:
		scanner.set_mode(ScanModes.NONE)


def ws_message(message):
	global reply_channel

	reply_channel = message.reply_channel
	print(message.content);
	# message.reply_channel.send({
	#     "text": message.content['text'],
	# })

