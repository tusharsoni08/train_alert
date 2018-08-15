from flask import Flask, request, jsonify
from scripts import pnrapi
import time
import re

app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
	req_data = request.get_json()
	print("\n************ DialogFlow Request Data **********")
	print(req_data)
	pnr_number = 0

	textIntent = (req_data['queryResult']['action'] == 'input.PNR'
		and req_data['queryResult']['intent']['displayName'] == "pnr_number")
	if textIntent:
		try:
			pnr_number = int(req_data['queryResult']['parameters']['number'])
		except Exception as e:
			pass

	#accept/decline request for push notification
	permissionIntent = (req_data['queryResult']['action'] == 'actions.intent.PERMISSION'
		and req_data['queryResult']['intent']['displayName'] == "notification_station")
	if permissionIntent:
		#when user accepted permission
		if req_data['originalDetectIntentRequest']['payload']['inputs'][0]['arguments'][0]['textValue'] == 'true':
			return processDetails(req_data['queryResult']['outputContexts'][0]['parameters']['number.original'],
									req_data['originalDetectIntentRequest']['payload']['user']['userId'])
			
		#when user declined permission
		if req_data['originalDetectIntentRequest']['payload']['inputs'][0]['arguments'][0]['textValue'] == 'false':
			return endConversation("No problem! see you next time.")

	if pnr_number != 0:
		pnr_number_str = str(pnr_number)
		if len(pnr_number_str) != 10:
			pnr_query = req_data['originalDetectIntentRequest']['payload']['inputs'][0]
			if pnr_query['intent'] == 'actions.intent.TEXT':
				text_data = pnr_query['arguments'][0]['textValue']
				query_str = text_data.replace(" ", "")

				numRegex = re.compile(r'\d{10}')
				matched_result = numRegex.search(query_str)
				isExpected = True

				if matched_result is not None:
					pnr_number_str = matched_result.group()
					n = query_str.index(pnr_number_str) + len(pnr_number_str)
					if n-1 < len(query_str)-1:
						if query_str[n].isdigit():
							isExpected = False

				if len(pnr_number_str) == 10 and isExpected:
					return processDetails(pnr_number_str, req_data['originalDetectIntentRequest']['payload']['user']['userId'])
				else:
					return jsonify(fulfillmentText="PNR Number has to be of 10 digits")
		else:
			
			#verify for update permission
			try:
				#PNR request with permission
				if req_data['originalDetectIntentRequest']['payload']['user']['permissions'] is not None:
					#check does this user in db, Yes->exit/No->continue
					return processDetails(req_data['queryResult']['outputContexts'][0]['parameters']['number.original'],
											req_data['originalDetectIntentRequest']['payload']['user']['userId'])
			except Exception as e:
				#PNR request without permission
				return askForPermission()
			
	else:
		return jsonify(fulfillmentText="Sorry, but I'm asking for PNR number")


def askForPermission():
	return jsonify({
		    "payload":{
		        "google":{
		            "expectUserResponse":True,
		            "systemIntent":{
		                "intent":"actions.intent.PERMISSION",
		                "data":{
		                    "@type":"type.googleapis.com/google.actions.v2.PermissionValueSpec",
		                    "permissions":[
		                        "UPDATE"
		                    ],
		                    "updatePermissionValueSpec":{
		                        "intent":"notification_station"
		                    }
		                }
		            }
		        }
		    }
		})


def endConversation(end_msg):
	return jsonify({
			   "payload":{
			      "google":{
			         "expectUserResponse":False,
			         "richResponse":{
			            "items":[
			               {
			                  "simpleResponse":{
			                     "textToSpeech": end_msg
			                  }
			               }
			            ]
			         }
			      }
			   }
			})


def processDetails(pnr, userId):
	p = pnrapi.PNRAPI(pnr, userId) #10-digit PNR Number
	start = time.time()
	response_status = p.request()
	print(time.time() - start)

	if response_status == True:
		print("Okay, I've set the reminder. Enjoy your journey!")
		return endConversation("Okay, I've set the reminder. Enjoy your journey!")
	elif response_status == None:
		print("Sorry, your train has departed from your destination station.")
		return endConversation("Sorry, your train has departed from your destination station.")
	elif response_status == 'Not Found':
		print("Sorry, your PNR number has been expired.")
		return endConversation("Sorry, your PNR number has been expired.")
	else:
		print("Currently service unavailable. Try again soon.")
		return endConversation("Currently service unavailable. Try again soon.")


if __name__ == '__main__':
	app.run(debug=False)