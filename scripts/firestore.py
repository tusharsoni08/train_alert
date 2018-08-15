import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os

class CloudFireStoreDB:

	def __init__(self, json, userId):
		#Initialize Cloud Firestore on server
		if (not len(firebase_admin._apps)):
			cred = credentials.Certificate({
			  "type": "service_account",
			  "project_id": os.environ.get('PROJECT_ID'),
			  "private_key_id": os.environ.get('PRIVATE_KEY_ID'),
			  "private_key": os.environ.get('PRIVATE_KEY').replace('\\n', '\n'),
			  "client_email": os.environ.get('CLIENT_EMAIL'),
			  "client_id": os.environ.get('CLIENT_ID'),
			  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
			  "token_uri": "https://accounts.google.com/o/oauth2/token",
			  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
			  "client_x509_cert_url": os.environ.get('CLIENT_CERT_URL')
			})
			default_app = firebase_admin.initialize_app(cred)
				
		self.json_data = json
		self.userId = userId

		print(self.json_data)
		self.set_data()


	def set_data(self):
		db = firestore.client()
		doc_ref = db.collection(u'users').document(self.userId)
		doc_ref.set({
			u'train_number': self.json_data["train_number"],
		    u'station_name': self.json_data["station_name"],
		    u'station_code': self.json_data["station_code"],
		    u'remaining_dist': self.json_data["remaining_dist"],
		    u'arrival_date': self.json_data['arrival_date'],
		    u'boarding_date': self.json_data['boarding_date']
		})
