from flask import Flask, request, jsonify
from scripts import pnrapi
import re
import time

app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
	req_data = request.get_json()
	print("************ REQUEST DATA **********")
	print(req_data)
	pnr_number = 0

	if req_data['queryResult']['intent']['displayName'] == "pnr_number":
		try:
			pnr_number = int(req_data['queryResult']['parameters']['number'])
		except Exception as e:
			print("PNR Number not found!")

	if pnr_number != 0:
		pnr_number_str = str(pnr_number)
		if len(pnr_number_str) != 10:
			#return jsonify(fulfillmentText="PNR Number has to be of 10 digits")
			return jsonify(
				{
					"fulfillmentText": "This is a text response",
					"followupEventInput": {
					    "name": "actions_intent_CONFIGURE_UPDATES",
					    "languageCode": "en-US"
					  }
				})
		else:
			p = pnrapi.PNRAPI(pnr_number_str) #10-digit PNR Number
			start = time.time()
			response_status = p.request()
			print(time.time() - start)

			if response_status == True:
				print("Okay, I've set the reminder")
				return jsonify(fulfillmentText="Okay, I've set the reminder")
			elif response_status == None:
				print("Sorry, your train has departed")
				return jsonify(fulfillmentText="Sorry, your train has departed")
			else:
				print("Currently service unavailable. Try again soon")
				return jsonify(fulfillmentText="Currently service unavailable. Try again soon")

if __name__ == '__main__':
	app.run(debug=False)