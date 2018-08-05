import requests
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time, os
from datetime import datetime, timedelta
import firestore

class PNRAPI:
		
	def __init__(self,pnr=""):

		self.response_json = {}
		self.pnr_data = ""
		# instantiate a chrome options object so we can set the size and headless preference etc.
		self.chrome_options = Options()
		self.chrome_options.binary_location = os.environ.get('GOOGLE_CHROME_BIN')
		self.chrome_options.add_argument("--headless")
		#self.chrome_options.add_argument("--window-size=414x736")
		self.chrome_options.add_argument("--disable-gpu")
		self.chrome_options.add_argument('--no-sandbox')
		self.chrome_options.add_argument("--disable-setuid-sandbox")
		prefs = {"profile.managed_default_content_settings.images":2}
		self.chrome_options.add_experimental_option("prefs",prefs)
		
		self.url_pnr = "https://www.railyatri.in/pnr-status/"
		self.url_train_spot = "https://enquiry.indianrail.gov.in/xyzabc/SelectedStationOfTrain?trainNo="
		self.pnr = pnr


	def request(self):
		# Search for details related PNR
		driver = webdriver.Chrome(chrome_options=self.chrome_options, executable_path=os.environ.get('CHROMEDRIVER_BIN'))

		try:
			driver.get(self.url_pnr + self.pnr)
			self.pnr_data = driver.find_element_by_xpath("(//div[@class='pnr-search-result-blk'])").text.split("\n")
			#make sure to return the request for opt-in chip (Till now it's verifed that PNR is valid)
		except Exception as e:
			try:
				driver.get(self.url_pnr + self.pnr)
				self.pnr_data = driver.find_element_by_xpath("(//div[@class='pnr-search-result-blk'])").text.split("\n")
			except Exception as e:
				return False
		
		if self.pnr_data[1] != self.pnr:
			return False
		else:
			return self.get_pnr_details(driver)


	def get_pnr_details(self, driver):
		
		#set pnr
		self.response_json["pnr"] = self.pnr
		
		#get train_number
		train_number = self.pnr_data[8]
		tarinNumRegex = re.compile(r'\d\d\d\d\d')
		self.response_json["train_number"] = tarinNumRegex.search(train_number).group()
		
		#set destination station name
		self.response_json["station_name"] = self.pnr_data[13].split(" | ")[0]

		#set destination station code
		self.response_json["station_code"] = self.pnr_data[13].split(" | ")[1]
		
		#set start time
		self.response_json["start_time"] = self.pnr_data[11]
		
		#set end time
		self.response_json["end_time"] = self.pnr_data[14]
		
		#set day of boarding
		self.response_json["boarding_date"] = self.pnr_data[18]
		
		#set journey time
		self.response_json["journey_time"] = self.pnr_data[16]
		
		#set platform number (tentative)
		self.response_json["pf"] = int(self.pnr_data[22])

		print(self.response_json)

		return self.fetch_running_status(driver)


	def fetch_running_status(self, driver):
		try:
			mobile_emulation = {"deviceMetrics": { "width": 360, "height": 640, "pixelRatio": 3.0 }, "userAgent": "Mozilla/5.0 (Linux; Android 8.1.0; en-us; Nexus 5 Build/JOP40D) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Mobile Safari/535.19" }
			self.chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
			driver = webdriver.Chrome(chrome_options=self.chrome_options, executable_path=os.environ.get('CHROMEDRIVER_BIN'))

			exp_arrival_date = self.find_arrival_date()
			arrival_date_formatted = datetime.strptime(str(exp_arrival_date), '%Y-%m-%d  %H:%M:%S').strftime('%d/%m/%Y')
			boarding_date_formatted = datetime.strptime(self.response_json["boarding_date"], '%d-%m-%Y').strftime('%d/%m/%Y')
			
			#url = self.url_train_spot + self.response_json["train_number"] + "&startDate=" + boarding_date_formatted + "&journeyStn=" + self.response_json["station_code"] #+ "&journeyDate=" + arrival_date_formatted + "&boardDeboard=0&langFile=props.en-us"
			url = self.url_train_spot + self.response_json["train_number"] + "&journeyStn=" + self.response_json["station_code"] + "&langFile=props.en-us"
			driver.get(url)

			#select destination arrival date
			select_element = Select(driver.find_element_by_id("journeyDate"))
			select_element.select_by_value(arrival_date_formatted)

			#check status and it should be "Yet to arrive"
			status = driver.find_element_by_id("qrdPosSttsMsg")
			if status.text != "" and status.text.lower() != "Yet to arrive".lower():
				return None
			
			#remaining KMs to arrive at destination station
			remaining_dist = driver.find_element_by_id("curPosMainDiv").find_element_by_class_name("kilometers")
			self.response_json["remaining_dist"] = int(remaining_dist.text)

			driver.quit()

			firestore.CloudFireStoreDB(self.get_json())
			
			return True

		except Exception as e:
			print(e)
			return False


	def find_arrival_date(self):
		boarding_date = datetime.strptime(self.response_json["boarding_date"] + " " + self.response_json["start_time"], "%d-%m-%Y %I:%M %p")
		journey_time = self.response_json["journey_time"].split(" ")
		numRegex = re.compile('\d+')
		journey_hrs = numRegex.search(journey_time[0]).group()
		journey_min = numRegex.search(journey_time[1]).group()
		arrival_date = boarding_date + timedelta(minutes=int(journey_min), hours=int(journey_hrs))
		self.response_json["arrival_date"] = arrival_date
		return arrival_date


	def get_json(self):
		return self.response_json
