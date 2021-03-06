import http.client, urllib.request, urllib.parse, urllib.error, base64
import json
from voiceit2 import VoiceIt2


class AzureHandler:
	def __init__(self, endpoint, subkey):
		self.endpoint = endpoint
		self.subkey = subkey

	# params: url path after domain, HTTP method, request body and HTTP headers
	def send_request(self, path, method="GET", b="", h=None):
		"""
		generic method for sending requests to the server using the http library
		all methods from the azure class use this method to send requests and 
		they just pass the respective params, headers, and path
		"""
		if h:
			headers = h
		else:
			headers = {
				'Ocp-Apim-Subscription-Key': self.subkey,
			}

		try:
			conn = http.client.HTTPSConnection(self.endpoint)
			conn.request(method, path, b, headers)
			response = conn.getresponse()
			data = response.read()
			conn.close()
			return response, data
		except Exception as e:
			return e


	def create_identification_profile(self):
		# returns user ID from profile created
		header_arg = {
			'Content-Type': 'application/json',
			'Ocp-Apim-Subscription-Key': self.subkey,
		}
		path_arg = "/spid/v1.0/identificationProfiles"
		method_arg = "POST"
		body = '{"locale":"en-us",}'

		response, data = self.send_request(path=path_arg, method=method_arg, b=body, h = header_arg)
		return data


	def enroll_identification_user(self, filename, profileId):
		# takes audio file and does API call, return operation URL for subsequent request
		headers_arg = {
		    'Content-Type': 'application/octet-stream',
		    'Ocp-Apim-Subscription-Key': self.subkey,
		}

		params = urllib.parse.urlencode({
    		# Request parameters
    		'shortAudio': 'true',
		})


		path_arg = "/spid/v1.0/identificationProfiles/{0}/enroll?{1}".format(profileId, params)
		method_arg = "POST"

		with open(filename, 'rb') as f:
			body = f.read()

		response, data = self.send_request(path=path_arg, method=method_arg, b=body, h = headers_arg)
		return response, data


	def get_identification_profile(self, userId):
		# return user object from API in JSON format
		path_arg = '/spid/v1.0/identificationProfiles/{0}'.format(profileId)
		response, data = self.send_request(path=path_arg)
		return data


	def get_all_identification_profiles(self):
		# returns list of user objects in JSON format
		path_arg = "/spid/v1.0/identificationProfiles"
		response, data = self.send_request(path=path_arg)
		return data


	def identify(self, filename, pids):
		"""
		gets audio file and does API call, returns operation URL for subsequent request
		 operation URL is in the HTTP headers
		"""
		headers = {
		    # Request headers
		    'Content-Type': 'application/octet-stream',
		    'Ocp-Apim-Subscription-Key': self.subkey,
		}
		params = urllib.parse.urlencode({"shortAudio": True})
		path_arg = "/spid/v1.0/identify?identificationProfileIds={0}&{1}".format(pids, params)
		method_arg = "POST"

		with open(filename, "rb") as f:
			body = f.read()

		response, data = self.send_request(path=path_arg, method=method_arg, b=body, h = header_arg)
		return response, data
	

	def create_verification_profile(self):
		"""
		creates profile on API and returns ID of profile created
		"""
		header_arg = {
			'Content-Type': 'application/json',
			'Ocp-Apim-Subscription-Key': self.subkey,
		}
		path_arg = "/spid/v1.0/verificationProfiles"
		method_arg = 'POST'
		body = '{"locale":"en-us",}'
		
		response, data = self.send_request(path=path_arg, method=method_arg, b=body, h = header_arg)
		return data


	def enroll_verification_user(self, filename, profileId):
		# gets audio file and does API call, returns operation URL for next operation in the headers
		headers_arg = {
		    'Content-Type': 'application/octet-stream',
		    'Ocp-Apim-Subscription-Key': self.subkey,
		}
		path_arg = "/spid/v1.0/verificationProfiles/{0}/enroll".format(profileId)
		method_arg = "POST"

		with open(filename, 'rb') as f:
			body = f.read()

		response, data = self.send_request(path=path_arg, method=method_arg, b=body, h = header_arg)
		return response, data


	def get_verification_profile(self, profileId):
		# return user object in JSON format
		path_arg = "/spid/v1.0/verificationProfiles/{0}".format(profileId)
		response, data = self.send_request(path=path_arg, method=method_arg, b=body, h = header_arg)
		return data


	def get_all_verification_profiles(self):
		# returns list of user objects in JSON format
		path_arg = "/spid/v1.0/verificationProfiles"
		response, data= self.send_request(path = path_arg)
		return data


	def delete_identification_profile(self, userId):

		path_arg = "/spid/v1.0/identificationProfiles/{0}".format(userId)
		response, data = self.send_request(path = path_arg, method = 'DELETE')
		return data


	def verify(self, filename, profileId):
		"""
		gets audio file, does API call and returns operation URL in the HTTP headers
		"""
		headers = {
            # Request headers
            'Content-Type': 'application/octet-stream',
            'Ocp-Apim-Subscription-Key': self.subkey,
        }
		path_arg = "/spid/v1.0/verify?verificationProfileId={0}".format(profileId)
		method_arg = 'POST'

		with open(filename, 'rb') as f:
			body = f.read()

		response, data = self.send_request(path=path_arg, method=method_arg, b=body, h = header_arg)
		return response, data


	def get_verification_phrases(self):
		# all the phrases available for the verfication process
		path_arg = "/spid/v1.0/verificationPhrases?locale=en-us"
		response, data = self.send_request(path=path_arg)
		return data


	def delete_verification_profile(self, userId):
		path_arg = "/spid/v1.0/verificationProfiles/{0}".format(userId)
		response, data = self.send_request(path = path_arg, method='DELETE')
		return data


	def get_operation(self, operationId):
		# given the operation Id, get the operation status from the specified URL
		path_arg = "/spid/v1.0/operations/{0}".format(operationId)
		response, data = self.send_request(path_arg)
		return data


	def parse_results(self, data):
		return json.loads(data.decode("ascii"))


class VoiceitHandler:
	def __init__(self, subkey="", token=""):
		"""if the subkey is empty, it means that the object will be created using a temporary 
		user token instead of an admin key,token pair. 
		"""
		if subkey == "":
			self.vt = VoiceIt2(token, "")
		else:
			self.vt = VoiceIt2(subkey, token)
    
    ########## user management ################################
	def create_user(self):
		return self.vt.create_user()


	def delete_user(self, userId):
		return self.vt.delete_user(userId)


	def get_users(self):
		return self.vt.get_all_users()


	def get_user_groups(self, userId):
		return self.vt.get_groups_for_user(userId)

	def get_supported_phrases(self):
		return self.vt.get_phrases("en-US")


	def create_token(self, userId, seconds = 60):
		"""Likely not going to use this method since the script will run on the server
		and key,token pair will be secret anyway.
		"""
		return self.vt.create_user_token(userId, seconds)


	def expire_tokens(self, userId):
		"""also, not likely to be used"""
		return self.vt.expire_user_tokens(userId)


	def enroll_user(self, profileId, phrase, filename):
		response = self.vt.create_voice_enrollment(profileId, "en-US", phrase, filename)
		return response

	def get_enrollments(self, userId):
		return self.vt.get_all_voice_enrollments(userId)


	def delete_enrollments(self, userId):
		return self.vt.delete_all_enrollments(userId)


	########## group management ################################
	def add_group(self, description=""):
		return self.vt.create_group(description)


	def add_user_to_group(self, groupId, userId):
		return self.vt.add_user_to_group(groupId, userId)


	def get_all_groups(self):
		return self.vt.get_all_groups()


	def get_group(self, groupId):
		return self.vt.get_group(groupId)


	def remove_user_from_group(self, groupId, userId):
		return self.vt.remove_user_from_group(groupId, userId)


	def delete_group(self, groupId):
		return self.vt.delete_group(groupId)


	#################################### ################################
	def identify(self, groupId, phrase, filename):
		response = self.vt.voice_identification(groupId, "en-US", phrase, filename)
		return response

	def verify(self, userId, phrase, filename):
		response = self.vt.voice_verification(userId, "en-US", phrase, filename)
		return response
