#mongomodels

import mongoengine
from mongoengine import *

connect("hackathon")

class Trashbin(Document):
	#Remember mongodb builtin id's
	name = StringField()
	dataID = IntField()

	location = GeoPointField()

	hasQrCode = BooleanField(default=False)

	emptiedLast = DateTimeField()
	isFull = BooleanField(default=False)
	reportedFull = DateTimeField()
