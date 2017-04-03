from django.contrib import admin

from .models import Book, Scan, Tag, Category, Author

admin.site.register([Book, Scan, Tag, Category, Author])
