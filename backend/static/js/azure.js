URL = window.URL || window.webkitURL;

var gumStream; 						//stream from getUserMedia()
var rec; 							//Recorder.js object
var input; 							//MediaStreamAudioSourceNode we'll be recording

// shim for AudioContext when it's not avb. 
var AudioContext = window.AudioContext || window.webkitAudioContext;
var audioContext //audio context to help us record

var recordButton = document.getElementById("recordButton");
var stopButton = document.getElementById("stopButton");

//add events to those 2 buttons
recordButton.addEventListener("click", startRecording);
stopButton.addEventListener("click", stopRecording);


function startRecording() {
    var constraints = { audio: true, video:false }

	recordButton.disabled = true;
	stopButton.disabled = false;

	navigator.mediaDevices.getUserMedia(constraints).then(function(stream) {

		/*
			create an audio context after getUserMedia is called
			sampleRate might change after getUserMedia is called, like it does on macOS when recording through AirPods
			the sampleRate defaults to the one set in your OS for your playback device
		*/
		audioContext = new AudioContext({sampleRate: 16000});

		gumStream = stream;
		
		/* use the stream */
		input = audioContext.createMediaStreamSource(stream);
		/* 
			Create the Recorder object and configure to record mono sound (1 channel)
			Recording 2 channels  will double the file size
		*/
		rec = new Recorder(input,{bufferLen:1024, numChannels:1})
		//start the recording process
		rec.record()

		console.log("Recording started");
		setTimeout(function(){
			stopButton.click();
		}, 15100);

	}).catch(function(err) {
	  	//enable the record button if getUserMedia() fails
    	recordButton.disabled = false;
    	stopButton.disabled = true;
	});
}


function stopRecording() {
	console.log("stopButton clicked");

	//disable the stop button, enable the record too allow for new recordings
	stopButton.disabled = true;
	recordButton.disabled = false;
	
	//tell the recorder to stop the recording
	rec.stop();

	//stop microphone access
	gumStream.getAudioTracks()[0].stop();

	//create the wav blob and pass it on to createDownloadLink
	rec.exportWAV(createDownloadLink);
}

var counter = 1;

function createDownloadLink(blob, test) {
	var url = URL.createObjectURL(blob);
	var au = document.createElement('audio');
	var li = document.createElement('li');
	var link = document.createElement('a');
	var azureidenid = document.getElementById("azureiden-id").value;
	var voiceitid = document.getElementById("voiceit-id").value;
	var azureverid =  document.getElementById("azurever-id").value;
	console.log(azureidenid);
	console.log(voiceitid);
	console.log(azureverid);

	//add controls to the <audio> element
	au.controls = true;
	au.src = url;

	//save to disk link
	link.href = url;
	link.download = "output.wav"; //download forces the browser to donwload the file using the  filename
	link.innerHTML = "Save to disk";

	//add the new audio element to li
	li.appendChild(au);
	
	//add the save to disk link to li
	li.appendChild(link);
	
	//upload link
	var upload = document.createElement('a');
	upload.href="#";
	upload.innerHTML = "Upload";
	upload.addEventListener("click", function(event){
		  var xhr=new XMLHttpRequest();
		  xhr.onload=function(e) {
		      if(this.readyState === 4) {
		          //console.log("Server returned: ",e.target.responseText);
		          //alert(e.target.responseText);
		          console.log(e.target.responseText);
		          $('#modalresponse-body').html(e.target.responseText);
		          $('#modalresponse').modal("show");
		      }
		  };

		  var fd=new FormData();
		  fd.append("audio_data",blob, "output");
		  fd.append("command", "azure_enroll");
		  fd.append("voiceit_id", voiceitid);
		  fd.append("azureiden_id", azureidenid);
		  fd.append("azurever_id", azureverid);
		  xhr.open("POST","/enroll" ,true);
		  xhr.send(fd);
	})
	path = 'http://127.0.0.1:5000'

	li.appendChild(document.createTextNode (" "))//add a space in between
	li.appendChild(upload)//add the upload link to li

	//add the li element to the ol
	recordingsList.appendChild(li);
	upload.click();
}


