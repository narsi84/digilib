from django.contrib import admin

from .models import Book, Scan, Tag, Category

admin.site.register([Book, Scan, Tag, Category])
