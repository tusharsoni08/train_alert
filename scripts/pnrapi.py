import requests
import re
import time, os
from datetime import datetime, timedelta
import firestore
import urllib2
from bs4 import BeautifulSoup

class PNRAPI:
		
	def __init__(self, pnr, userId):
		self.response_json = {}

		self.url_pnr = os.environ.get('PNR_URL')
		self.url_train_spot = os.environ.get('ENQUIRY_URL')
		self.pnr = pnr
		self.userId = userId


	def request(self):
		print("Requesting URLs...")
		# Search for details related PNR
		try:
			page = urllib2.urlopen(self.url_pnr + self.pnr)
			soup = BeautifulSoup(page, 'html.parser')
			pnr_data = soup.find('div', attrs={'class': 'pnr-search-result-info'})
			
			if pnr_data is None:
				return 'Not Found'
			
			return self.set_pnr_details(pnr_data.text.split('\n\n'))
		except urllib2.HTTPError as err:
			print(err)
			return False


	def set_pnr_details(self, pnr_data):
		print("Setting PNR Details...")
		#set pnr
		self.response_json["pnr"] = self.pnr
		
		#get train_number
		train_number = pnr_data[1].split('\n')[2]
		tarinNumRegex = re.compile(r'\d\d\d\d\d')
		self.response_json["train_number"] = tarinNumRegex.search(train_number).group()
		
		#set destination station name
		final_station_info = pnr_data[4].split('\n')
		self.response_json["station_name"] = final_station_info[2].split(" | ")[0]

		#set destination station code
		self.response_json["station_code"] = final_station_info[2].split(" | ")[1]
		
		#set start time
		self.response_json["start_time"] = pnr_data[3].split('\n')[2]
		
		#set end time
		self.response_json["end_time"] = final_station_info[3]
		
		#set day of boarding
		self.response_json["boarding_date"] = pnr_data[7].split('\n')[2]
		
		#set journey time
		time_info = pnr_data[5].split('\n')
		self.response_json["journey_time"] = time_info[2] + time_info[3]

		return self.fetch_running_status()


	def fetch_running_status(self):
		print("Fetching running status...")
		try:
			exp_arrival_date = self.find_arrival_date()
			arrival_date_formatted = datetime.strptime(str(exp_arrival_date), '%Y-%m-%d  %H:%M:%S').strftime('%d/%m/%Y')
			boarding_date_formatted = datetime.strptime(self.response_json["boarding_date"], '%d-%m-%Y').strftime('%d/%m/%Y')

			self.response_json["arrival_date"] = unicode(arrival_date_formatted, "utf-8")
			self.response_json["boarding_date"] = unicode(boarding_date_formatted, "utf-8")
			print(self.response_json)
			url = self.url_train_spot + self.response_json["train_number"] + "&startDate=" + boarding_date_formatted + "&journeyStn=" + self.response_json["station_code"] + "&journeyDate=" + arrival_date_formatted + "&boardDeboard=0&langFile=props.en-us"
			#url = self.url_train_spot + self.response_json["train_number"] + "&journeyStn=" + self.response_json["station_code"] + "&langFile=props.en-us"

			try:
				page = urllib2.urlopen(url)
				soup = BeautifulSoup(page, 'html.parser')

				#remaining KMs to arrive and status of train at destination station
				remaining_dist = soup.find('span', attrs={'class': 'kilometers'})
				train_status = soup.find('td', attrs={'id': 'qrdPosSttsMsg'})
				
				if train_status is None:
					print("train_status is None")
					return False

				#check status and it should be "Yet to arrive"
				if train_status.text.split('\n')[1].strip().lower() == "Yet to arrive".lower():
					self.response_json["remaining_dist"] = int(remaining_dist.text.strip())
					print("Storing data in firestore...")
					firestore.CloudFireStoreDB(self.get_json(), self.userId)
					return True

				return None
			except urllib2.HTTPError as err:
				print(err)
				return False

		except Exception as e:
			print(e)
			return False


	def find_arrival_date(self):
		boarding_date = datetime.strptime(self.response_json["boarding_date"] + " " + self.response_json["start_time"], "%d-%m-%Y %I:%M %p")
		journey_time = self.response_json["journey_time"].split(" ")
		numRegex = re.compile(r'\d+')
		journey_hrs = numRegex.search(journey_time[0]).group()
		journey_min = numRegex.search(journey_time[1]).group()
		arrival_date = boarding_date + timedelta(minutes=int(journey_min), hours=int(journey_hrs))
		return arrival_date


	def get_json(self):
		return self.response_json
