#flaskapp.py

from flask import Flask, request, url_for, redirect, render_template, flash
from mongomodels import *
from threading import Thread

from qrcode.image.pure import PymagingImage

import os, json, datetime, qrcode


app = Flask(__name__, static_folder=os.path.join('..', 'static'))
app.config['DEBUG'] = True
app.config['pathToStatic'] = os.path.join('..', 'static')
app.config['pathToStatic'] = os.path.join(os.getcwd(), '..', 'static')

app.config['pathToQR'] = os.path.join(os.getcwd(), '..', 'static', 'qr')
turku = [60.451493, 22.268831] 

app.secret_key = 'This is a secret'

def trashToJson(trash):
	json = ({"name":trash.name, \
			"dataID":trash.dataID, \

			"location": trash.location, \
			"isFull": trash.isFull
			})
	#print json
	return json

@app.route("/")
def test():
	return render_template("index.html")


@app.route("/findclosesttrash")
def closestTrash():
	longitude = request.args.get('long', '0')
	latitude  = request.args.get('lat', '0')

	longitude= float(longitude)
	latitude = float(latitude)

	coords = [longitude, latitude]

	#print "Found closest trashbin: " + str(longitude) + " " + str(latitude)
	#print coords

	closest = Trashbin.objects(location__near=coords,isFull=False).first()

	js = json.dumps(trashToJson(closest))
	return js

	#return "This function returns a json with the closest trashcan " + \
	#		str(closest.dataID) + " " + str(closest.location) + "\n" + trashToJson(closest)


@app.route("/findclosetrash")
def closeTrash():
	longitude = request.args.get('long', '0')
	latitude  = request.args.get('lat', '0')

	longitude= float(longitude)
	latitude = float(latitude)

	coords = [longitude, latitude]
	#print coords

	closest = Trashbin.objects(location__near=coords, isFull=False)[1:5]
	bins = list()
	for t in closest:
		bins.append(trashToJson(t))

	js = json.dumps({"trashbins":bins})
	return js
	

@app.route("/trash/<trashID>")
def getTrash(trashID):
	trash = Trashbin.objects(dataID=trashID).first()
	return render_template('trash.html', trash=trash)


@app.route("/trash/<trashID>/json")
def getTrashJson(trashID):
	trash = Trashbin.objects(dataID=trashID).first()
	js = json.dumps(trashToJson(trash))
	return js


@app.route("/trash/<trashID>/full", methods=['GET','POST'])
def trashFull(trashID):
	t = Trashbin.objects(dataID = trashID).first()
	t.isFull = True
	t.reportedFull = datetime.datetime.now()

	t.save()
	print "Trasbin " + str(trashID) + " was set to full"

	#If request is from browser, redirect to view, else return 200
	if request.method == "GET":
		flash('Trashbin has been reported as full')
		return  redirect(url_for("getTrash", trashID=trashID))
	else:
		print "Returning post request"
		return "Success " + str(trashID), 200 
	return "Success" + trashID + " is full"


@app.route("/trash/<trashID>/emptied", methods=['GET','POST'])
def trashEmptied(trashID):
	t = Trashbin.objects(dataID = trashID).first()
	t.isFull = False
	t.emptiedLast = datetime.datetime.now()

	t.save()

	flash("Trashbin " + str(t.dataID) + " was emptied")

	if request.method == "POST":
		return redirect(url_for("fullBins"))
	return  redirect(url_for("getTrash", trashID=trashID))
	return "Success", 200


@app.route("/loadData")
def loadData():
	if app.debug:
		json_data = open(os.path.abspath("Roskikset_geojson.geojson"))
		print json_data
		data = json.load(json_data)

		listid = 0
		dataList = []
		noids = len(data["features"])
		dataList.append(0)
		noids = noids - 1
		while listid <= noids:
			trash = Trashbin()
			coord = data["features"][listid]["geometry"]["coordinates"]
			text = data["features"][listid]["properties"]["ID"]
			coordlist = list()
			coordlist.append(float(coord[0]))
			coordlist.append(float(coord[1]))

			trash.location = coordlist
			#print coordlist
			#print type(coordlist)
			try:
				text = int(text)
			except TypeError:
				text = 0

			trash.dataID = text
			trash.save()

			listid = listid + 1

		noOfEntries = len(Trashbin.objects())


		return "Loading data," + str(noOfEntries) + " found trashbins"
	return "This method is only available in debug mode"


@app.route("/deldata")
def delData():
	if app.debug:
		Trashbin.objects.delete()

		return "Deleted data"
	return "This method is only available in debug mode"



#Generates testdatapoints. 
@app.route("/testdata")
def testData():
	if app.debug:
		Trashbin.objects.delete()

		turkuX = 60.451493
		turkuY = 22.268831

		for i in range(100):
			t = Trashbin()
			t.dataID = i
			t.location = [turkuX+(i/1000.0), turkuY+(i/1000.0)]
			t.save()
		return "Generated " + str(i) + " testdata"
	return "This method is only available in debug mode"


#
@app.route("/qrprint")
def qrPrint():
	page = request.args.get('p', '0')
	page = int(page)
	bins = Trashbin.objects(dataID__gte=page*12	, dataID__lt=(page+1)*12)

	if (len(bins)< 2):
		if len(bins)<1:
			return 	 render_template('qrprint.html', bin=bins, page=0)
		return render_template('qrprint.html', bin=bins, page=page)
	return render_template('qrprint.html', bins=bins, page=page)


def asynQrCodes(arg):
	url = ""
	for i in arg:
		url += i
	print url
	trashbins = Trashbin.objects(hasQrCode=True)
	print "Generating " + str(len(trashbins)) + " qr codes"

	for bin in trashbins:
		if bin.hasQrCode:
			f = open(os.path.join(app.config['pathToQR'], str(bin.dataID)+".png"),"w")
			#qr = qrcode.make(url+str(bin.dataID)+"/full", image_factory=PymagingImage)
			qr = qrcode.make(url+str(bin.dataID), image_factory=PymagingImage)
			qr.save(f)
			print "generated qr " + url + str(bin.dataID)
			bin.hasQrCode = True
			bin.save()

	print type(trashbins)


@app.route("/generateQr")
def generateQrCodes():
	if app.debug: 
		trashbins = Trashbin.objects(hasQrCode=False)
		baseUrl = "http://trashmate.danielwarna.com"
		urlSuffix = url_for("getTrash", trashID=1)
		urlSuffix = urlSuffix[:-1]

		url = baseUrl + urlSuffix

		thread = Thread(target = asynQrCodes, args = [url])
		thread.start()
	#	for bin in trashbins:
	#		thread = Thread(target=asynQrCodes, args=[trashbins])
	#		thread.start()
	#		qr = qrcode.make(baseUrl+url_for("getTrash", trashID=bin.dataID), image_factory=PymagingImage)
	#		qr.save(f)
	#		print "Generated qr for" + str(bin.dataID) + "  " + baseUrl+url_for("getTrash", trashID=bin.dataID)	

		return "Generated x qrcodes"
	return "This method is only available in debug mode"


@app.route("/fullbins")
def fullBins():
	bins = Trashbin.objects(isFull=True)

	return render_template('fullbins.html',bins=bins)


@app.route("/fullbins/json")
def fullBinsJson():
	trashbins = Trashbin.objects(isFull=True)

	bins = list()
	for t in trashbins:
		bins.append(trashToJson(t))


	return json.dumps({"trashbins":bins})


@app.route("/debug")
def debug():
	assert True == False, "Don't panic! You're here by request of debug()"


if __name__ == '__main__':
	app.run()

#Enables the interactive debugger
#http://codeseekah.com/2012/10/28/dubugging-flask-applications-under-uwsgi/
if (app.debug):
	from werkzeug.debug import DebuggedApplication
	app.wsgi_app = DebuggedApplication(app.wsgi_app, True)
