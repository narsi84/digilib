from __future__ import unicode_literals

from django.db import models

class Tag(models.Model):
	name = models.CharField(max_length = 100)
	def __str__(self):
		return self.name
	
class Category(models.Model):
	name = models.CharField(max_length = 100)
	def __str__(self):
		return self.name

class Book(models.Model):
	created_time = models.DateTimeField('Created on', auto_now_add=True)
	modified_time = models.DateTimeField('Modified on', auto_now=True)
	name = models.CharField(max_length = 100)
	category = models.ForeignKey(Category)
	tags = models.ManyToManyField(Tag, related_name='book', null=True)
	def __str__(self):
		return self.name
	
class Scan(models.Model):
	created_time = models.DateTimeField('Created on', auto_now_add=True)
	page = models.IntegerField()
	loc = models.CharField(max_length = 256)
	book = models.ForeignKey(Book, on_delete=models.CASCADE)
		
