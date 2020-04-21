from speak import speak
import record
import speech_recognition as sr
from request_handler import general_request, file_request

r = sr.Recognizer()
m = sr.Microphone()
countdown_cmd = 'mpg321 ttsfiles/countdown.mp3' 


def file_to_text(filename):
    # takes audio file and returns the corresponding string from transcription
    with sr.AudioFile(filename) as source:
        audio = r.record(source)
    try:
        s = r.recognize_google(audio)
        return s
    except Exception as e:
        return str(e)


def pretty_list(ls):
    # in case RPi is connected to a screen, it will display the list of avaiable phrases nicely
    s = ""
    for item in ls:
        s += "\t"+ item +"\n"
    return s


def start_voiceit_registration():
    try:
        askname_filename = 'askname'
        audio_length = 5
        
        # ask for name and convert speech input to text
        tts("please say your name", askname_filename)
        askname_cmd = 'mpg321 ttsfiles/{}.mp3'.format(askname_filename)
        os.system(askname_cmd)
        record.record(audio_length, "name.wav")
        name = file_to_text("name.wav")

        # send request to local server 
        path = '/start_voiceit_registration'
        method = 'POST'
        body = "{'name':'{0}', 'source': 'raspberry'}".format(name)
        response = general_request(path, method, body)
        return response
    except Exception as e:
        return str(e)


def voiceit_enrollment(uid, phrases):
    """
    takes userId and phrases, records user saying the phrase
    and sends request to server with audio file and userId 
    before each recording, the program will do a countdown using text to speech
    after receiveng server response, it converts it to audio to provide feedback to user
    """
    try:
        iterations = 3
        audio_length = 5
        enrollment_filename = 'enrollment.wav'
        response_filename = 'voiceit_enrollment_response'
        
        print("supported phrases: \n", pretty_list(phrases))

        count = 1
        path = '/voiceit_enrollment'
        filename = enrollment_filename
        method = 'POST'
        
        # 3 enrollments required for this API, keep trying until 3 successful enrollments are made
        while count <= iterations:
            # takes the audio file passed to it as argument and plays it for voice interaction
            os.system(countdown_cmd)
            record.record(audio_length, enrollment_filename)
            phrase = file_to_text(enrollment_filename)
            params = {
                'phrase': phrase,
                'filename': filename,
                'userId': uid
            }
            
            #send request to local server (middleware)
            enrollment_response = file_request("/voiceit_enrollment", filename, params = params)
            enrollment_response_code = enrollment_response.get('responseCode')
            
            # if enrollment attempt is successful, provide user feedback and increment count
            if enrollment_response_code == 'SUCC':
                count += 1
                text = "attempt {0} of enrollment successful".format(count)
                tts(text, response_filename)
            else:
                tts(enrolmment_response['message'], response_filename)

            enrollment_cmd = 'mpg321 ttsfiles/{}.mp3'.format(response_filename)
            os.system(enrollment_cmd)

        os.system("mpg321 ttsfiles/EnrollmentSuccess.mp3")
        
        # delete audio files created every time 
        #if not explicitly deleted, they can cause problems for future requests
        os.remove(enrollment_filename)
        os.remove(response_filename)
        return enrollment_response
    except Exception as e:
        print(str(e))
        return str(e)


def voiceit_verification(groupId):
    """
    takes the voiceit group id, records audio to be used for identification & verification
    first performs the identification, if successful it proceeds to verification
    if any of the 2 fails, it just returns error message
    """
    try:
        # identification process 
        verification_filename = 'verify.wav'
        identification_response_filename = 'identification_response'
        audio_length = 5
        verification_response_filename = 'verification_response'

        # do countdown and record
        os.system("mpg321 ttsfiles/startedVerification.mp3")
        os.system(countdown_cmd)
        record.record(audio_length, verification_filename)
        phrase = file_to_text(verification_filename)
        params = {
            'phrase': phrase,
            'filename': verification_filename,
            'groupId': groupId
        }

        # send request to server, with audio file and params as HTTP headers
        identification_response = file_request('/voiceit_identify', verification_filename, params)
        responseCode = identification_response.get('responseCode')
        
        # if identification is successful proceed to verification using the recorded file
        # and the userId returned in the response to identification
        if responseCode == 'SUCC':
            uid = identification_response.get('userId')
            name = identification_response.get('username')
            params = {
                'phrase': phrase,
                'filename': verification_filename, 
                'userId': uid
            }
            
            # if the name of the user is available, use that name. Otherwise, just say user
            if name:
                s = "First step completed, {0} was successfully identified. Please wait for the complete verification".format(name)
            else:
                s = "First step completed, user was successfully identified. Please wait for the complete verification"
            
            # provide feedback of identification request 
            tts(s, identification_response_filename)
            identification_cmd = 'mpg321 ttsfiles/{}.mp3'.format(identification_response_filename)
            os.system(identification_cmd)
            
            # send verification request
            verification_response = file_request('/voiceit_verify', verification_filename, params)
            verification_response_code = verification_response.get('responseCode')
           
            # if request is successful, get the confidence
            if verification_response_code == 'SUCC':
                confidence = verification_response.get('confidence')
                st = "successfully verified user with confidence: {0}".format(confidence) 
            else:
                st = verification_response.get('message')
            
            # provide feeback of verification request
            tts(st, verification_response_filename)
            verification_cmd = 'mpg321 ttsfiles/{}.mp3'.format(verification_response_filename) 
            os.system(verification_cmd)
            
            # explicitly remove all audio files used for voice interaction
            os.remove(identification_response_filename)
            os.remove(verification_response_filename)
            os.remove(verification_filename)
            return verification_response
        else:
            # error message of identification
            st = identification_response.get("message")
            tts(st, identification_response_filename)
            identification_cmd = 'mpg321 ttsfiles/{}.mp3'.format(identification_response_filename)
            os.system(identification_cmd)
            
            os.remove(identification_response_filename)
            os.remove(verification_response_filename)
            os.remove(verification_filename)
            return identification_response
    except Exception as e:
        print(str(e))
        return str(e)


def start_azure_registration():
    """
    creates profiles for both identification and verification
    returns the respective IDs and the phrases available 
    """
    try:
        path = '/start_azure_registration'
        response = general_request(path=path, message="POST")
        return response
    except Exception as e:
        print(str(e))
        return str(e)


def azure_identification_enrollment(userId):
    """
    given an user Id, record the audio file and send it to the server along with the Id
    """
    try:
        enrollment_filename = 'identification_enrollment.wav'
        response_filename = 'idenfication_response'
        audio_length = 30
        path = "/azure_identification_enrollment"
        params = {
            'userId': userId,
            'filename': enrollment_filename
        }
        # do countdown before starting to record and then send request with audio file
        os.system(countdown_cmd)
        record.record(audio_length, enrollment_filename)
        identification_response = file_request(path, enrollment_filename, params)
        responseCode = identification_response.get('responseCode')
        
        # provide audio feedback to the user
        if responseCode == 'SUCC':
            tts('successfully enrolled user for identification', response_filename)
        else:
            message = idenfication_response.get('message')
            if message:
                tts(message, response_filename)
            else:
                tts('error trying to enroll user for identification', response_filename)

        speech_cmd = 'mpg321 ttsfiles/{}.mp3'.format(response_filename)
        os.system(speech_cmd)
        os.remove(response_filename)
        os.remove(enrollment_filename)
        return identification_response
    except Exception as e:
        print(str(e))
        return str(e)


def azure_verification_enrollment(userId, phrases):
    """
    given an user Id, record the audio file and send it to the server along with the Id
    """
    try:
        enrollment_filename = 'verification_enrollment.wav'
        response_filename = 'verification_response'
        iterations = 3
        audio_length = 15
        path = '/azure_verification_enrollment'
        params = {
            'userId': userId,
            'filename': enrollment_filename
        }

        print("phrases: ", pretty_list(phrase))
        
        count = 1
        # 3 registrations needed, keep trying until 3 successfull attemps have been made
        while count <= iterations:
            os.system(countdown_cmd)
            record.record(audio_length, enrollment_filename)
            enrollment_response = file_request(path, enrollment_filename, params)
            responseCode = enrollment_response.get('responseCode')
            
            # provide audio feedback to the user
            if responseCode == 'SUCC':
                st = "attempt {} of azure verification enrollment successfull".format(count)
                tts(st, response_filename)
                count += 1
            else:
                tts("error trying to enroll user for verification ", response_filename)

            speech_cmd = 'mpg321 ttsfiles/{}.mp3'.format(response_filename)
            os.system(speech_cmd)

        os.system("mpg321 ttsfiles/EnrollmentSuccess.mp3")
        os.remove(enrollment_filename)
        os.remove(response_filename)
        return enrollment_response
    except Exception as e:
        print(str(e))
        return str(e)


def azure_identification():
    """
    record user audio and send request for identification
    """
    try:
        identification_filename = 'azure_identification.wav'
        response_filename = 'identification_response'
        audio_length = 15
        path = '/azure_identify'
        params = {
            'filename': identification_filename,
        }
        
        os.system(countdown_cmd)
        record.record(audio_length, identification_filename)
        identification_response = file_request(path, identification_filename, params)
        responseCode = idenfication_response.get('identification_response')
        
        # provide audio feedback to user
        if responseCode == 'SUCC':
            name = idenfication_response.get('username')
            if name:
                st = "First step completed, {0} was successfully identified. Please wait for the complete verification".format(name)
            else:
                st = "First step completed, user was successfully identified. Please wait for the complete verification"
            
        else:
            st = "Error identifying user"

        tts(st, response_filename)
        identification_cmd = 'mpg321 ttsfiles/{0}.mp3'.format(response_filename)
        os.system(identification_cmd)
        os.remove(identification_filename)
        os.remove(response_filename)
        return identification_response
    except Exception as e:
        print(str(e))
        return str(e)
        

def azure_verification(userId):
    """
    record user audio and send request for identification
    """
    try:
        verification_filename = 'azure_verification.wav'
        response_filename = 'verification_response'
        audio_length = 15
        path = '/azure_verify'
        params = {
            'filename': verification_filename,
            'userId': userId
        }

        os.system(countdown_cmd)
        record.record(audio_length, verification_filename)
        verification_response = file_request(path, verification_filename, params)
        responseCode = verification_response.get('responseCode')
        
        # provide audio feedback to user
        if responseCode = 'SUCC':
            confidence = verification_response.get('confidence')
            st = "successfully verified user with confidence: {0}".format(confidence) 
        else:
            st = verification_response.get('message')

        tts(st, response_filename)
        verification_cmd = 'mpg321 ttsfiles/{}.mp3'.format(response_filename)
        os.system(verification_cmd)
        os.remove(verification_filename)
        os.remove(response_filename)
        return verification_response
    except Exception as e:
        print(str(e))
        return str(e)

