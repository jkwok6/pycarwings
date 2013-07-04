import requests

def requestRoute(start, end):

	#start = "1001 W. Peltason Dr, Irvine,CA"
	#end = "Claremont,CA"

	url = 'http://maps.google.com/maps/nav?key=YOUR-MAP-KEY&output=json&q=from%3A'+start+ ' to%3A'+end

	data = requests.get(url=url).json()
	directions = data['Directions']['Routes'][0]['Steps']

	coordList = [(x['Point']['coordinates'][1], x['Point']['coordinates'][0]) for x in directions]

	coordString = ''
	for i in coordList:
		coordString = coordString + str(i[0])+','+str(i[1])+'|'

	elevationURL = "http://maps.googleapis.com/maps/api/elevation/json?sensor=false&path=" + coordString[:-1] + '&samples=10'

	#print elevationURL
	#eleData = requests.get(url = elevationURL)
	return data

def getElevations(coordList):
	coordString = ''
	elevationURL = "http://maps.googleapis.com/maps/api/elevation/json?sensor=false&locations="
	for i in coordList:
		coordString = coordString + str(i[0])+','+str(i[1])+'|'
	reqURL = elevationURL + coordString[:-1]

	response = requests.post(url = reqURL)
	if response.status_code != 200:
		print "error, code is", response.status_code
		raise Exception("error: response code was not 200")
	
	elevations = []
	for result in response.json()['results']:
		elevations.append(result['elevation'])
	return elevations
