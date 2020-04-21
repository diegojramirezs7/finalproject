import http.client, urllib.request, urllib.parse, urllib.error, base64
import requests

def general_request(path, method="GET", body="", h=None):
	"""
	If no header param is given, content type of body defaults to application/json
	otherwise, header is overwritten
	"""
	if h:
		headers = h
	else:
		headers = {
	    	'Content-Type': 'application/json',
		}

	try:
		conn = http.client.HTTPConnection("localhost:5000")
		conn.request(method, path, body, headers)
		response = conn.getresponse()
		data = response.read()
		print(data.decode("ascii"))
		conn.close()
		return data
	except Exception as e:
		print(e)


def file_request(path, filename, params="", method='POST'):
	endpoint = "http://localhost:5000"
	if method == 'POST':
		url = endpoint+path
		with open(filename, 'rb') as f:
			r = requests.post(url, files={filename: f}, headers=params)
			print(str(r))

		return r
	else:
		return "wrong method passed"


