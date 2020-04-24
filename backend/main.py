from flask import Flask, render_template, request, make_response, redirect, url_for
from api_handler import AzureHandler, VoiceitHandler
import json
import speech_recognition as sr
from model import Model
import time
import os

r = sr.Recognizer()

# API key and endpoint can be found on the Azure portal, under cognitive services
_pkey = "704c3dd99d09405f962d9dfce5719f13"
_endpoint= 'voice-recog.cognitiveservices.azure.com'
azure = AzureHandler(_endpoint, _pkey)

# Voiceit Key and Token can be found on the API website: https://voiceit.io/console
# an account should be made first
voiceit = VoiceitHandler("key_d79251d085214874b7479cdf67cd40b8", "tok_3f628df367944320a359510086825836")

# Mysql credentials (host, user, password, DB)
model = Model("localhost", 'root', 'Mysql_pw1?', 'silverservers')
app = Flask(__name__)


######################################## Helper Methods #############################
def start_registration(name):
	"""
	Creates profiles in voiceit, azure identification and azure verification.
	All the Ids returned by creating the profiles are saved to the DB along with the user name.
	By default all users are added to the "general" group.
	"""
	try:
		voiceit_string = voiceit_registration()
		voiceit_dic = json.loads(voiceit_string)
		azure_string = start_azure_registration()
		
		azure_dic = json.loads(azure_string)

		values = {
			'name': name,
			'voiceitUserId': voiceit_dic['voiceitUserId'],
			'phrases': voiceit_dic['voiceitPhrases'],
			'azureIdentificationUserId': azure_dic['azureIdenProfileId'],
			'azureVerificationUserId': azure_dic['azureVerProfileId'],
			'azurePhrases': azure_dic['azurePhrases'],
			'responseCode': 'SUCC'
		}
		db_response = model.save_user(voiceit_id=values['voiceitUserId'], azure_ver_id=values['azureVerificationUserId'], 
				azure_iden_id = values['azureIdentificationUserId'], name=name)

		
		db_response = model.get_user(values['voiceitUserId'])
		if db_response:
			model.add_user_to_group(db_response[0])
		
		return values
	except Exception as e:
		dic = {
			'responseCode': 'FAIL',
			'message': str(e)
		}
		return dic


def file_to_text(path):
	"""Converts an audio file to text, returns the string"""
	with sr.AudioFile(path) as source:
		audio = r.record(source)

	try:
		text = r.recognize_google(audio)
		return text
	except Exception as e:
		return str(e)


def remove_id(message):
	if 'usr_' in message:
		position = msg.index('usr_')
		uid = message[position: position + 36]
		st = message.replace(uid, "")
	elif 'grp_' in message:
		position = msg.index('grp_')
		gid = message[position: position + 36]
		st = message.replace(gid, "")
	else:
		st = message

	return st


def get_operation_id(operationUrl):
	"""
	azure operation id is found at the end of an operation URL
	the operation id is always 36 characters long, so the last 36 characters are extracted
	"""
	return operationUrl[-36:]


def parse_results(resp):
	# from binary to python dictionary
	return json.loads(resp.decode("ascii"))


######################################## Web Interface Requests #############################
@app.route("/", methods=['POST', 'GET'])
def index():
	# by default, the index redirects to /users
	if request.method == 'GET':
		return redirect('/users')
	else:
		return "Invalid HTTP method"

		
@app.route("/enroll", methods=['POST', 'GET'])
def enroll():
	"""
	This method handles enrollments when user was already created, 
	"""
	try:
		if request.method == 'GET':
			return render_template("enroll.html", dic = "")
		elif request.method == 'POST':
			command = request.form.get('command')
			if command == 'start_registration':
				# creates profiles with respective IDs and redirects to page where user can do the voiceit Enrollments
				fullname = request.form.get('fullname')
				registration_response = start_registration(fullname)
				if registration_response['responseCode'] == 'SUCC':
					return render_template("registration.html", dic = registration_response)
				else:
					return render_template('enroll.html', dic = registration_response)
			elif command == 'voiceit_enroll':
				# receives audio file and performs the API call for enrollment
				f = request.files['audio_data']
				userId = request.form.get('userId');
				path = "/Users/diego_ramirezs/documents/flaskapp/audio_files/{0}.wav".format(userId)
				f.save(path)
				phrase = file_to_text(path)
				response = voiceit.enroll_user(userId, phrase, path)
				if response['responseCode'] == 'SUCC':
					model.update_user(voiceit_id=userId, voiceit_enrolled=1)
				os.remove(path)
				return response['message']
			elif command == 'azure_enroll':
				# receives audio file and performs the API call for enrollment for both Identification and verification
				f = request.files['audio_data']
				voiceitId = request.form.get('voiceit_id')
				azureidenId = request.form.get('azureiden_id')
				azureverId = request.form.get('azurever_id')
				path = "/Users/diego_ramirezs/documents/flaskapp/audio_files/{0}.wav".format("voiceitId")
				f.save(path)
				identification_response = azure_enroll_identification(azureidenId, path)
				verification_response = azure_enroll_verification(azureverId, path)
				if identification_response['responseCode'] == 'SUCC' and verification_response['responseCode'] == 'SUCC':
					response_dic = {
						'responseCode': 'SUCC',
						'identification_response': identification_response['message'],
						'verification_response': verification_response['message']
					}
				else:
					response_dic = {
						'responseCode': 'FAIL',
						'message': 'Unable to enroll user for azure'
					}

				response_dic_string = json.dumps(response_dic)
				os.remove(path)
				return response_dic_string
		
			return "Incorrect Command Sent"
	except Exception as e:
		return str(e)


@app.route("/prepare_voiceit_enrollment", methods=['POST', 'GET'])
def prepare_voiceit_enrollment():
	"""
	prepares page for voiceit enrollment. Retrieves name, phrases and id.
	Then, redirects to enrollment page where users can do the recording
	"""
	try:
		if request.method == 'POST':
			voiceitId = request.form.get('voiceitUserId')
			voiceitId = voiceitId.strip()

			user_db = model.get_user(voiceitId)
			if user_db:
				name = user_db[1]
				voiceit_phrases_resp = voiceit.get_supported_phrases()
				if voiceit_phrases_resp['responseCode'] == 'SUCC':
					voiceit_phrases = [x['text'] for x in voiceit_phrases_resp['phrases']]

					content = {
						'name': name,
						'voiceitUserId': voiceitId,
						'phrases': voiceit_phrases
					}
				else:
					return "Error During Voiceit API call, unable to retrieve phrases"

				return render_template("registration.html", dic=content)
			else:
				return "Error Retrieving Data from DB"
		else:
			return "Incorrect HTTP method used"
	except Exception as e:
		return str(e)


@app.route("/prepare_azure_enrollment", methods=['POST', 'GET'])
def prepare_azure_enrollment():
	"""
	prepares page for azure enrollment. Retrieves name, phrases and id.
	Then, redirects to enrollment page where users can do the recording
	"""
	try:
		if request.method == 'POST':
			voiceitId = request.form.get('voiceitId')
			voiceitId = voiceitId.strip()

			user_db = model.get_user(voiceitId)
			if user_db:
				name = user_db[1]
				azureIdenId = user_db[3]
				azureVerId = user_db[4]

				azure_phrases_resp = azure.get_verification_phrases()
				if azure_phrases_resp:
					azure_phrases_resp = parse_results(azure_phrases_resp)
					azure_phrases = [x['phrase'] for x in azure_phrases_resp]

					content = {
						'name': name,
						'azureIdenId': azureIdenId,
						'azureVerId': azureVerId,
						'voiceitId': voiceitId,
						'phrases': azure_phrases
					}

					return render_template("azure_registration.html", dic=content)
				else:
					return "Error During Voiceit API call, unable to retrieve phrases"
			else:
				return "Error Retrieving Data from DB"
		else:
			return "Incorrect HTTP method used"

	except Exception as e:
		return str(e)


@app.route("/users", methods = ['POST', 'GET'])
def get_users():
	"""gets all users from DB and displays them on a table"""
	try:
		if request.method == 'GET':
			users = model.get_users()
			return render_template('users.html', dic=users)
		else:
			return "Incorrect HTTP method used"
	except Exception as e:
		return str(e)


@app.route("/users/<command>", methods = ['POST', 'GET'])
def update_user(command):
	"""
	The only 2 updates allowed are deleting the user or changing the name
	The IDs cannot be modified since they are managed by the respective APIs
	"""
	try:
		if request.method == 'GET':
			users = model.get_users()
			return render_template('users.html', dic = users)
		else:
			if command == 'delete_user':
				content = request.get_json()
				userId = content.get('voiceit_id')
				userId = userId.strip()
				delete_response = delete_user(userId)
				return delete_response
			elif command == 'update_name':
				content = request.get_json()
				userId = content.get('voiceit_id')
				userId = userId.strip()
				newname = content.get('name')
				newname = newname.strip()
				db_response = model.update_user(userId, name=newname)
				if db_response == "success":
					msg = "Successfully updated the user: {0}".format(newname)
					response_dic = {
						'responseCode': 'SUCC',
						'message': msg
					}
					response_dic_string = json.dumps(response_dic)
					return response_dic_string
				else:
					return "Error Ocurred Updating the DB"
	except Exception as e:
		return str(e)


def delete_user(userId):
	"""Deletes user from the APIs and from the local DB"""
	try:
		user = model.get_user(userId)
		if user:
			vresponse = voiceit.delete_user(user[2])
			a1response = azure.delete_identification_profile(user[3])
			a2response = azure.delete_verification_profile(user[4])
			dbresponse = model.delete_user(userId)

			name = user[1]
			
			msg = "Successfully deleted {0} from the system".format(name)

			response_dic = {
				'responseCode': 'SUCC', 
				'message': msg
			}
			response_dic_string = json.dumps(response_dic)
			return response_dic_string
		else:
			st = "Unable to find user with ID: {0}".format(userId)
			return st
	except Exception as e:
		print(str(e))
		return str(e)


@app.route("/groups", methods=['POST', 'GET'])
def get_groups():
	# returns list of groups
	try:
		if request.method == 'GET':
			general = model.get_groups()
			return render_template('groups.html', dic=general)
		else:
			return "Incorrect HTTP method used"
	except Exception as e:
		return str(e)


@app.route("/group/<groupId>", methods=['POST', 'GET'])
def get_group(groupId):
	# returns a list of users belonging to a group
	try:
		if request.method == 'POST':
			users_db = model.get_users_from_group(groupId)
			if users_db:
				user_list = []
				for user in users_db:
					user_list.append((user[0], user[1], user[5]))

				users_string = str(user_list)
				content = {
					'user_list': user_list
				}
				return content
			else:
				return "EMPTY"
		else:
			return "Incorrect HTTP method used"
	except Exception as e:
		return str(e)


@app.route("/groups/<command>", methods=['POST', 'GET'])
def update_group(command):
	"""
	Only 4 allowed updates: create group, delete group, update name and add user to group
	all of those methods are handled directly by the Model, this is mostly the interface
	The Azure API doesn't have explicit groups. So, it'll be handled by the local DB.

	"""
	try:
		if request.method == 'POST':
			if command == 'create':
				req = request.get_json()
				groupName = req.get('name')
				groupName = groupName.strip()
				
				voiceit_response = voiceit.add_group(groupName)
				if voiceit_response['responseCode'] == 'SUCC':
					voiceitId = voiceit_response['groupId']
					db_response = model.create_group(groupName, voiceitId)
					if db_response == 'success':
						msg = "Successfully created group: {0}".format(groupName)
					else:
						msg = db_response

					return msg

				else:
					return "Failed to Create Voiceit Group"

			elif command == 'delete':
				req = request.get_json()
				groupName = req.get('name')
				groupName = groupName.strip()
				voiceitId = req.get('voiceitId')
				voiceitId = voiceitId.strip()
				
				voiceit_response = voiceit.delete_group(voiceitId)
				db_reponse = model.delete_group(groupName)	
				if db_reponse == 'success':
					msg = "Successfully deleted group group: {0}".format(groupName)
				else:
					msg = db_reponse

				return msg

			elif command == 'update_name':
				content = request.get_json()
				groupId = content.get('groupId')
				groupName = content.get('name')
				groupName = groupName.strip()
				db_response = model.update_group(groupId, groupName)
				if db_response == "success":
					msg = "Successfully updated the group: {0}".format(groupName)
				else:
					msg = "Error Ocurred Updating the DB"

				return msg

			elif command == 'add_user_to_group':
				content = request.get_json()
				groupId = content.get('groupId')
				userId = content.get('userId')
				st = "the group id is: {0} and the user id is: {1}".format(groupId, userId)
				users = model.get_users()
				userIds = [x[0] for x in users]
				userId = int(userId)
				if userId in userIds:
					db_response = model.add_user_to_group(userId, groupId)
					if db_response == 'success':
						msg = "Successfully added user to the DB"
					else:
						msg = db_response
				else:
					msg = "Id entered doesn't exist"
				
				return msg
		else:
			return "Incorrect HTTP method"
	except Exception as e:
		return str(e)


@app.route('/test', methods=['POST', 'GET'])
def test():
	try:
		if request.method == 'POST':
			command = request.form.get('command')
			voiceitId = request.form.get('voiceitUserId')
			print(voiceitId)
			d = {
				'command': command,
				'voiceitUserId': voiceitId
			}
			return render_template("registration.html", dic=d)
		else:
			return "hello there"
	except Exception as e:
		return str(e)


######################################## VoiceIt Requests from Raspberry Pi #############################
def voiceit_registration():
	# used by general registration method
	try:
		voiceit_resp = voiceit.create_user()
		if voiceit_resp['responseCode'] == 'SUCC':
			voiceit_userId = voiceit_resp['userId']

		voiceit_phrases_resp = voiceit.get_supported_phrases()
		if voiceit_phrases_resp['responseCode'] == 'SUCC':
			voiceit_phrases = [x['text'] for x in voiceit_phrases_resp['phrases']]

		resp_dic = {
			'voiceitUserId': voiceit_userId,
			'voiceitPhrases': voiceit_phrases
		}
		response_dic_string = json.dumps(resp_dic)
		return response_dic_string
	except Exception as e:
		print(str(e))
		return str(e)


@app.route("/start_voiceit_registration", methods = ['POST', 'GET'])
def start_voiceit_registration():
	# creates the profile in the API, saves it to the DB and returns ID and phrases 
	try:
		voiceit_resp = voiceit.create_user()
		if voiceit_resp['responseCode'] == 'SUCC':
			voiceit_userId = voiceit_resp['userId']

		voiceit_phrases_resp = voiceit.get_supported_phrases()
		if voiceit_phrases_resp['responseCode'] == 'SUCC':
			voiceit_phrases = [x['text'] for x in voiceit_phrases_resp['phrases']]

		resp_dic = {
			'voiceitUserId': voiceit_userId,
			'voiceitPhrases': voiceit_phrases
		}

		req = request.get_json()
		name = req.get('name')

		model.save_user(name = name, voiceit_id = voiceit_userId)
		model.add_user_to_group(voiceit_userId, groupId = 1)

		resp_dic_string = json.dumps(resp_dic)
		return resp_dic_string
	except Exception as e:
		return "Error: {0}".format(e)


@app.route("/voiceit_enrollment", methods=['POST', 'GET'])
def voiceit_enrollment():
	# receives audio file from RPi, performs the API call for enrollment and returns appropriate response
	try:
		if request.method == 'POST':
			phrase = request.headers.get('phrase')
			filename = request.headers.get('filename')
			uid = request.headers.get('userId')
			file_path = "/Users/diego_ramirezs/documents/flaskapp/audio_files/"+filename
			
			f = request.files[filename]
			f.save(file_path)
			db_tuple = model.get_user(uid)
			name = db_tuple[1]
			
			res = voiceit.enroll_user(uid, phrase, file_path)
			if res['responseCode'] == 'SUCC':
				response_dic = {
					'responseCode': res['responseCode'],
					'message': 'Successfully enrolled user',
					'name': name
				}
			else:
				message = res['message']
				st = remove_id(message)

				response_dic = {
					'responseCode': res['responseCode'],
					'message': st
				}

			response_dic_string = json.dumps(response_dic)
			os.remove(file_path)
			return response_dic_string
		else:
			return "{'responseCode': 'BDRQ', 'message': 'Incorrect HTTP method'}"
	except Exception as e:
		return str(e)

@app.route('/voiceit_identify', methods=['POST', 'GET'])
def voiceit_identify():
	# receives audio file and performs the API call, 
	# if successful returns confidence and user data, else return custom error message
	try:
		if request.method == 'POST':
			phrase = request.headers.get('phrase')
			filename = request.headers.get('filename')
			groupId = request.headers.get('groupId')
			file_path = "/Users/diego_ramirezs/documents/flaskapp/audio_files/"+filename

			f = request.files[filename]
			f.save(file_path)

			identification_response = voiceit.identify(groupId, phrase, file_path)
			responseCode = identification_response.get('responseCode')
			if responseCode == 'SUCC':
				userId = identification_response.get('userId')
				message = identification_response.get('message')
				clean_message = remove_id(messsage)
				confidence = identification_response.get('confidence')

				db_tuple = model.get_user(userId)
				if db_tuple:
					name = db_tuple[1]
				else:
					name = ''

				response_dic = {
					'responseCode': responseCode,
					'userId': userId,
					'message': clean_message,
					'username': name,
					'confidence': confidence
				}
				response_dic_string = json.dumps(response_dic)
				os.remove(file_path)
				return response_dic_string
			else:
				message = identification_response.get('message')
				clean_message = remove_id(message)
				response_dic = {
					'responseCode': responseCode,
					'message': clean_message,
				}
				response_dic_string = json.dumps(response_dic)
				os.remove(file_path)
				return response_dic
		else:
			return "{'responseCode': 'BDRQ', 'message': 'Incorrect HTTP method'}"
	except Exception as e:
		print(str(e))
		return str(e)


@app.route("/voiceit_verify", methods=['POST', 'GET'])
def voiceit_verify():
	# receives audio file and performs the API call, 
	# if successful returns confidence and user data, else return custom error message
	try:
		if request.method == 'POST':
			phrase = request.headers.get('phrase')
			filename = request.headers.get('filename')
			userId = request.headers.get('userId')
			file_path = "/Users/diego_ramirezs/documents/flaskapp/audio_files/"+filename+".wav"

			f = request.files[filename]
			f.save(file_path)

			verification_response = voiceit.verify(userId, phrase, file_path)
			responseCode = verification_response.get('responseCode')
			if responseCode == 'SUCC':
				confidence = verification_response.get('confidence')
				message = verification_response.get('message')
				clean_message = remove_id(message)
				response_dic = {
					'responseCode': responseCode,
					'message': clean_message,
					'confidence': confidence,
				}
				response_dic_string = json.dumps(response_dic)
				os.remove(file_path)
				return response_dic_string
			else:
				message = verification_response.get('message')
				clean_message = remove_id(message)
				response_dic = {
					'responseCode': responseCode,
					'message': clean_message,
				}
				response_dic_string = json.dumps(response_dic)
				os.remove(file_path)
				return response_dic_string
		else:
			return "{'responseCode': 'BDRQ', 'message': 'Incorrect HTTP method'}"
	except Exception as e:
		print(str(e))
		return str(e)


######################################## Azure Requests #################################


######################################## Common methods #################################
@app.route("/start_azure_registration", methods=['POST', 'GET'])
def start_azure_registration():
	# creates Identification and Verification Profiles and returns the respective IDs and phrases
	try:
		azure_resp = azure.create_identification_profile()
		azure_resp = parse_results(azure_resp)	
		azureIdenProfileId = azure_resp['identificationProfileId']
		
		azure_resp = azure.create_verification_profile()
		azure_resp = parse_results(azure_resp)
		azureVerProfileId = azure_resp['verificationProfileId']
		
		azure_phrases_resp = azure.get_verification_phrases()
		azure_phrases_resp = parse_results(azure_phrases_resp)
		azure_phrases = [x['phrase'] for x in azure_phrases_resp]

		response_dic = {
			'azureIdenProfileId': azureIdenProfileId,
			'azureVerProfileId': azureVerProfileId,
			'azurePhrases': azure_phrases
		}

		response_dic_string = json.dumps(response_dic)
		return response_dic_string
	except Exception as e:
		response_dic = {
			'responseCode': 'FAIL',
			'message': str(e)
		}
		response_dic_string = json.dumps(response_dic)
		return response_dic_string


def get_azure_operation(operationId):
	"""
	All operations on azure that handle audio files don't return a direct response to the requests.
	They respond with an Operation URL and Operation Id where the results of the operation can be found
	Subsequent request to that url should be made until a suitable response is obtained. 
	Usually the operation results are ready within 5 seconds, if they are not ready they will return: processing
	This method keeps sending requests to that URL with a small delay between each one until we obtain a succeeded/failed response
	"""
	count = 1
	delay = 1.5
	attempts = 5
	while count <= attempts:
		operation_response = azure.get_operation(operationId)
		operation_response = parse_results(operation_response)
		status = operation_response.get('status')
		print(operation_response)
		if status == 'succeeded':
			result = operation_response.get('processingResult')
			message = json.dumps(result)
			response_dic = {
				'responseCode': 'SUCC', 
				'message': message
			}
			response_dic_string = json.dumps(response_dic)
			return response_dic_string
		elif status == 'failed':
			response_dic = {
				'responseCode': 'FAIL',
				'message': 'failed to process request'
			}
			response_dic_string = json.dumps(response_dic)
			return response_dic_string
		
		count += 1
		time.sleep(delay)

	response_dic = {
		'responseCode': 'INCM',
		'message': 'unable to complete azure enrollment'
	}

	response_dic_string = json.dumps(response_dic)
	return response_dic_string

######################################## Azure helper methods for Web Interface  #################################

def azure_enroll_identification(userId, path):
	# receives audio file and performs the API call, 
	# then calls get_azure_operation to get the appropriate results
	try:
		identification_response, data = azure.enroll_identification_user(path, userId)
		statusCode = identification_response.status
		if 200 <= statusCode < 300:
			operation_url = identification_response.getheader('Operation-Location')
			operation_id = get_operation_id(operation_url)
			operation_response = get_azure_operation(operation_id)
			return operation_response
		else:
			data = parse_results(data)
			error = data.get('error')
			message = error.get('message')
			
			if not message:
				message = "unable to process azure enrollment request"
			
			response_dic = {
				'responseCode': 'FAIL',
				'message': message
			}
			response_dic_string = json.dumps(response_dic)
			
			return response_dic_string
	except Exception as e:
		print(str(e))
		return str(e)


def azure_enroll_verification(userId, path):
	# receives audio file and performs the API call, 
	# then calls get_azure_operation to get the appropriate results
	try:
		verification_response, data = azure.enroll_verification_user(file_path, userId)
		statusCode = verification_response.status
		if 200 <= statusCode < 300:
			operation_url = verification_response.getheader('Operation-Location')
			operation_id = get_operation_id(operation_url)
			operation_response = get_azure_operation(operation_id)
			return operation_response
		else:
			data = parse_results(data)
			error = data.get('error')
			message = error.get('message')
			
			if not message:
				message = "unable to process azure enrollment request"
			
			response_dic = {
				'responseCode': 'FAIL',
				'message': message
			}
			response_dic_string = json.dumps(response_dic)
			
			return response_dic_string
	except Exception as e:
		print(str(e))
		return str(e)


######################################## Azure Requests from Raspberry Pi ########################################

@app.route("/azure_identification_enrollment", methods=['POST', 'GET'])
def azure_identification_enrollment():
	# receives audio file and performs the API call, 
	# then calls get_azure_operation to get the appropriate results
	try:
		if request.method == 'POST':
			userId = request.headers.get('userId')
			filename = request.headers.get('filename')
			file_path = "/Users/diego_ramirezs/documents/flaskapp/audio_files/"+filename

			f = request.files[filename]
			f.save(file_path)
		
			identification_response, data = azure.enroll_identification_user(file_path, userId)
			#headers = identification_response.msg
			statusCode = identification_response.status
			if 200 <= statusCode < 300:
				operation_url = identification_response.getheader('Operation-Location')
				operation_id = get_operation_id(operation_url)
				operation_response = get_azure_operation(operation_id)
				os.remove(file_path)
				return operation_response
			else:
				# data = b'{ "error": { "code": "NotFound", "message": "Resource or path can\'t be found." } }'
				data = parse_results(data)
				error = data.get('error')
				message = error.get('message')
				if not message:
					message = "unable to process azure enrollment request"
				response_dic = {
					'responseCode': 'FAIL',
					'message': message
				}
				response_dic_string = json.dumps(response_dic)
				os.remove(file_path)
				return response_dic_string
		else:
			return "{'responseCode': 'BDRQ', 'message': 'Incorrect HTTP method'}"

	except Exception as e:
		print(str(e))
		return str(e)


@app.route("/azure_verification_enrollment", methods=['POST', 'GET'])
def azure_verification_enrollment():
	# receives audio file and performs the API call, 
	# then calls get_azure_operation to get the appropriate results
	try:
		if request.method == 'POST':
			userId = request.headers.get('userId')
			filename = request.headers.get('filename')
			file_path = "/Users/diego_ramirezs/documents/flaskapp/audio_files/"+filename

			f = request.files[filename]
			f.save(file_path)

			verification_response, data = azure.enroll_verification_user(file_path, userId)
			statusCode = verification_response.status
			if 200 <= statusCode < 300:
				operation_url = verification_response.getheader('Operation-Location')
				operation_id = get_operation_id(operation_url)
				operation_response = get_azure_operation(operation_id)
				os.remove(file_path)
				return operation_response
			else:
				data = parse_results(data)
				error = data.get('error')
				message = error.get('message')
				if not message:
					message = "unable to process azure enrollment request"
				response_dic = {
					'responseCode': 'FAIL',
					'message': message
				}
				response_dic_string = json.dumps(response_dic)
				os.remove(file_path)
				return response_dic_string
		else:
			return "{'responseCode': 'BDRQ', 'message': 'Incorrect HTTP method'}"

	except Exception as e:
		print(str(e))
		return str(e)


@app.route("/azure_identification", methods=['POST', 'GET'])
def azure_identification():
	# receives audio file and performs the API call, 
	# then calls get_azure_operation to get the appropriate results
	try:
		if request.method == 'POST':
			# need to get the list of all the users to be passed to azure.identify()
			group_tuple = model.get_group('general')
			group_id = group[0]
			users = model.get_users_from_group(group_id)
			userId_list = [item[2] for item in users]
			string_list = ",".join(userId_list)

			filename = request.headers.get('filename')
			file_path = "/Users/diego_ramirezs/documents/flaskapp/audio_files/"+filename

			f = request.files[filename]
			f.save(file_path)

			identification_response = azure.identify(file_path, string_list)
			statusCode = verification_response.status
			# if response status code is ok, proceed to get operation results, otherwise return error
			if 200 <= statusCode < 300:
				operation_url = identification_response.getheader('Operation-Location')
				operation_id = get_operation_id(operation_url)
				operation_response = get_azure_operation(operation_id)
				operation_response = json.loads(operation_response)
				if operation_response['response'] == 'SUCC':
					message = operation_response['message']
					message = json.loads(message)
					identficationId = message.get('identifiedProfileId')
					confidence = message.get('confidence')
					user_tuple = model.get_user_from_azure_id(identficationId)
					if user_tuple:
						verificationId = user_tuple[4]
						response_dic = {
							'responseCode': 'SUCC',
							'verificationId': verificationId,
							'confidence': confidence,
							'name': user_tuple[1]
						}
						response_dic_string = json.dumps(response_dic)
						return response_dic_string

				os.remove(file_path)
				return operation_response
			else:
				data = parse_results(data)
				error = data.get('error')
				message = error.get('message')
				if not message:
					message = 'Unable to process azure verification request request'
				response_dic = {
					'responseCode': 'FAIL',
					'message': message
				}
				
				response_dic_string = json.dumps(response_dic)
				os.remove(file_path)
				return response_dic_string
		else:
			return "{'responseCode': 'BDRQ', 'message': 'Incorrect HTTP method'}"
	except Exception as e:
		print(str(e))
		return str(e)


@app.route("/azure_verification", methods=['POST', 'GET'])
def azure_verification():
	# receives audio file and performs the API call, 
	# then calls get_azure_operation to get the appropriate results
	try:
		if request.method == 'POST':
			userId = request.headers.get('userId')
			filename = request.headers.get('filename')
			file_path = "/Users/diego_ramirezs/documents/flaskapp/audio_files/"+filename

			f = request.files[filename]
			f.save(file_path)

			verification_response, data = azure.verify(file_path, userId)
			statusCode = verification_response.status
			# if response status code is ok, proceed to get operation results, otherwise return error
			if 200 <= statusCode < 300:
				operation_url = verification_response.getheader('Operation-Location')
				operation_id = get_operation_id(operation_url)
				operation_response = get_azure_operation(operation_id)
				os.remove(file_path)
				return operation_response
			else:
				data = parse_results(data)
				error = data.get('error')
				message = error.get('message')
				if not message:
					message = 'Unable to process azure verification request request'
				response_dic = {
					'responseCode': 'FAIL',
					'message': message
				}
				
				response_dic_string = json.dumps(response_dic)
				os.remove(file_path)
				return response_dic_string
		else:
			return "{'responseCode': 'BDRQ', 'message': 'Incorrect HTTP method'}"
	except Exception as e:
		print(str(e))
		return str(e)


if __name__ == "__main__":
	app.run()
