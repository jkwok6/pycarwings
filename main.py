from flask import Flask, session, redirect, render_template, request, flash, jsonify
from directions import requestRoute, getElevations
app = Flask(__name__)
import yaml
from pycarwings import connection, userservice, vehicleservice
import time
from pdb import set_trace as trace

username = 'jonkwok'
password = 'gogiants'

battChargeConversion = [8,15,22,29,36,44,51,57,64,71,78,84,92]
@app.route('/getCarData')
def getCarData():
	print "getting car data"
	c = connection.Connection(username, password)
	u = userservice.UserService(c)
	d = u.login_and_get_status()
	vin = d.user_info.vin
	print "sleeping 20 seconds..."
	time.sleep(20)
	status = u.get_latest_status(vin)
	statusString = yaml.dump(status)
	#trace()
	split = statusString.split('\n')
	batt = split[4]
	start = batt.find("'")
	end = batt.find("'",start+1)
	battPower = int(batt[start+1:end])
	battPowerConverted = battChargeConversion[battPower]
	
	
	
	return jsonify({'status':'ok', 'batteryRemaining':battPowerConverted})

@app.route('/')
def main():
	return render_template("main.html")

@app.route('/directions-list')
def directionsList():
	start = request.args.get('start')
	dest = request.args.get('dest')
	chargeLevel = request.args.get('chargeLevel')
	
	if not start:
		start = '1001 W. Peltason Dr. Irvine, CA'
	if not dest:
		dest = '340 E. Foothill Blvd, Claremont, CA'
	return render_template("directions-list.html", charge_state='71', start=start,dest=dest, chargeLevel=chargeLevel)

# [0-14,15-29,30-44,45-59,60+]
energyBins = [44, 84,90,114,233]
speedInterval = 15

#[0-9,10-19,20-29,30-39,40-49,50-59,60-69,70+]
energyBinsElevation = [
(-2.11165,29.7104),
(1.74161,74.2946),
(25.3193,101.77),
(29.2636,119.032),
(32.9691,139.737),
(31.0045,168.537),
(17.0672,217.228),
(12.8766,274.809),
]
speedIntervalElev = 10



@app.route('/calcPowerUsage', methods=['POST','GET'])
def calcPowerUsage():
	data = request.json
	start = data['start']
	dest = data['dest']
	
	oneWayUsage, routeData = calcOneWayUsage(start, dest)
	usageReturn, _ = calcOneWayUsage(dest, start)
	
	oneWayScaled = round(oneWayUsage/10000, 1)
	returnScaled = round(usageReturn/10000, 1)
	
	return jsonify({'routeData':routeData, 'totalPowerUsage':oneWayScaled+returnScaled, 'oneWayUsage':oneWayScaled})

def calcOneWayUsage(start, dest):
	data = requestRoute(start, dest)
	routeSteps = data['Directions']['Routes'][0]['Steps']
	#list of tuples for each leg of (<miles/hr>,<duration,seconds>, usage, <HTML description>)
	coordinates = []
	for step in routeSteps:
		coordinate = step['Point']['coordinates']
		coordinate = (coordinate[1],coordinate[0])
		coordinates.append(coordinate)
	elevations = getElevations(coordinates)
	
	totalPowerUsage = 0
	routeData = []
	for counter, step in enumerate(routeSteps[:-1]):
		
		seconds = step['Duration']['seconds']
		meters = step['Distance']['meters']
		miles = meters/1609.34
		miles = round(miles,2)
		#usage, milesPerHour = calcStepUsage(step)
		usage, milesPerHour = calcStepUsageElevation(step, elevations, counter)
		totalPowerUsage += usage
		description = step['descriptionHtml']
		routeData.append({'milesPerHour':milesPerHour, 'seconds':seconds, 'powerUsage':round(usage/10000,2), 'routeDescription':description, 'miles':miles})
		
	'''startEndDetails = data['Placemark']
	startStreet = startEndDetails[0]['AddressDetails']['Country']['AdministrativeArea']['SubAdministrativeArea']['Locality']['Thoroughfare']['ThoroughfareName']
	startCity = startEndDetails[0]['AddressDetails']['Country']['AdministrativeArea']['SubAdministrativeArea']['Locality']['LocalityName']
	startZip = startEndDetails[0]['AddressDetails']['Country']['AdministrativeArea']['SubAdministrativeArea']['Locality']['PostalCode']['PostalCodeNumber']
	startState = startEndDetails[0]['AddressDetails']['Country']['AdministrativeArea']['AdministrativeAreaName']

	endStreet = startEndDetails[1]['AddressDetails']['Country']['AdministrativeArea']['SubAdministrativeArea']['Locality']['Thoroughfare']['ThoroughfareName']
	endCity = startEndDetails[1]['AddressDetails']['Country']['AdministrativeArea']['SubAdministrativeArea']['Locality']['LocalityName']
	endZip = startEndDetails[1]['AddressDetails']['Country']['AdministrativeArea']['SubAdministrativeArea']['Locality']['PostalCode']['PostalCodeNumber']
	endState = startEndDetails[1]['AddressDetails']['Country']['AdministrativeArea']['AdministrativeAreaName']
	
	startCityStateZip = startCity + ', ' + startState + ' ' + startZip
	endCityStateZip = endCity + ', ' + endState + ' ' + endZip
	
	startDetails = {'street':startStreet, 'cityStateZip':startCityStateZip}
	endDetails = {'street':endStreet, 'cityStateZip':endCityStateZip}'''
	
	#return totalPowerUsage, routeData, startDetails, endDetails
	return totalPowerUsage, routeData
	
	
def calcStepUsage(step):
	seconds = step['Duration']['seconds']
	meters = step['Distance']['meters']
	milesPerHour = 2.23694*float(meters)/seconds
	bin = min(int(milesPerHour)/speedInterval,len(energyBins)-1)
	usage = energyBins[bin]*seconds
	return usage, milesPerHour

def calcStepUsageElevation(step, elevations, counter):
	seconds = step['Duration']['seconds']
	meters = step['Distance']['meters']
	milesPerHour = 2.23694*float(meters)/seconds
	
	eleChange = (elevations[counter+1] - elevations[counter])*3.28084
	bin = min(int(milesPerHour)/speedIntervalElev,len(energyBinsElevation)-1)
	
	usage = energyBinsElevation[bin][0]*eleChange + energyBinsElevation[bin][1]*seconds
	return usage, milesPerHour
	
	
	
	
	
		


if __name__ == '__main__':
    app.run(debug=True)