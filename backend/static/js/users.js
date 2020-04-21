var user_dic = {};
var target;
var children;

function showModal(){
  target = event.target.parentElement;
  children = target.children;
  user_dic['userId'] = children[0].innerHTML;
  user_dic['username'] = children[1].innerHTML;
  user_dic['voiceit-id'] = children[2].innerHTML;
  user_dic['azureiden-id'] = children[3].innerHTML;
  user_dic['azurever-id'] = children[4].innerHTML;

  $('#usermodal-title').html(user_dic['username']);
  $('#modal-user-id').html(user_dic['userId']);
  $('#modal-user-name').val(user_dic['username']);
  $('#modal-voiceit-id').html(user_dic['voiceit-id']);
  $('#modal-azureiden-id').html(user_dic['azureiden-id']);
  $('#modal-azurever-id').html(user_dic['azurever-id']);
  var message = "are you sure you want to delete user with name: "+children[1].innerHTML;
  $('#confirmation-box').html(message);

  $('#showModalBtn').click();
}

function deleteUser(){
  var voiceitId = user_dic['voiceit-id'];
  var content = {
    "voiceit_id": voiceitId
  }
  $.ajax({
    type: "POST",
    url: "/users/delete_user",
    data: JSON.stringify(content),
    contentType: "application/json",
    success: function(result){
      var res = JSON.parse(result);
      $('#confirmation-cancel').click();
      $('#usermodal-close').click();

      $('#modalresponse-body').html(res['message']);
    }
  });
}

function reload(){
  location.reload();
}

function updateName(){
  user_dic['username'] = $('#modal-user-name').val();
}


function saveClose(){
  var username = user_dic['username'];
  var voiceitId = user_dic['voiceit-id'];
  var content = {
    "voiceit_id": voiceitId,
    "name": username
  };
  $.ajax({
    type: "POST",
    url: "/users/update_name",
    data: JSON.stringify(content),
    contentType: "application/json",
    success: function(result){
      var res = JSON.parse(result);

      $('#modalresponse-body').html(res['message']);
      $('#modalresponse').modal('show');
    }
  });
}

function enrollVoiceit(){
  var voiceitId = user_dic['voiceit-id'];
  $('#voiceitUserId').val(voiceitId);
  console.log($('#voiceitUserId').val());
  $('#enroll-voiceit-form').submit();
}

function enrollAzure(){
  var voiceitId = user_dic['voiceit-id'];
  $('#voiceitId').val(voiceitId);
  console.log($('#voiceitUserId').val());
  $('#enroll-azure-form').submit();
}




