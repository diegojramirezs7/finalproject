var target;
var children;
var group_dic = {};

function showGroup(){
  target = event.target.parentElement;
  children = target.children;
  group_dic['groupId'] = children[0].innerHTML;
  group_dic['name'] = children[1].innerHTML;
  group_dic['voiceitId'] = children[2].innerHTML;
  var groupId = group_dic['groupId'].trim();
  $('#groupmodal').modal('show');
  $('#modal-group-id').html(group_dic['groupId']);
  $('#modal-group-name').val(group_dic['name']);
  $("#groupmodal-title").html(group_dic['name']);
  
  var path = "/group/"+groupId;
  var message = "are you sure you want to delete user with name: "+children[1].innerHTML;
  $('#confirmation-box').html(message);
  $.ajax({
    type: "POST",
    url: path,
    success: function(result){
      //var result_list = JSON.parse(result);
      if(result === 'EMPTY'){
        $('#user_table').html("NO users yet!");
      }else{
        var user_list = result['user_list'];
        var content = "<tr><th>Id </th><th>Name</th><th>Created</th></tr>";
        for(var i = 0; i<user_list.length; i++){
          content += "<tr>"
          for (var j = 0; j<user_list[i].length; j++){
            content += "<td>"+user_list[i][j]+"</td>"
          }
          content += "</tr>"
        }
        $('#user_table').html(content);
      }
      
    }
  });
}


function saveClose(){
  var groupName = group_dic['name'];
  var groupId = group_dic['groupId'];

  console.log(groupName);
  var content = {
    "groupId": groupId,
    "name": groupName
  };
  $("#user_table").html("");
  $.ajax({
    type: "POST",
    url: "/groups/update_name",
    data: JSON.stringify(content),
    contentType: "application/json",
    success: function(result){
      $('#modalresponse-body').html(result);
      $('#modalresponse').modal('show');
    }
  });
}


function createGroup(){
  var groupName = $('#modal-ask-name').val();
  var content = {
    "name": groupName
  }
  $.ajax({
    type: "POST",
    url: "/groups/create",
    data: JSON.stringify(content),
    contentType: "application/json",
    success: function(result){
      $('#modalresponse-body').html(result);
      $('#modalresponse').modal('show');
    }
  });
}


function deleteGroup(){
  var groupName = group_dic['name'];
  var voiceitId = group_dic['voiceitId'];
  var content = {
    "name": groupName,
    "voiceitId": voiceitId
  };
  $.ajax({
    type: "POST",
    url: "/groups/delete",
    data: JSON.stringify(content),
    contentType: "application/json",
    success: function(result){
      $('#modalresponse-body').html(result);
      $('#modalresponse').modal('show');
    }
  });
}


function addUserToGroup(){
  var groupId = group_dic['groupId'];
  var userId = $('#modalUserId').val();
  var content = {
    "userId": userId, 
    "groupId": groupId
  }
  $.ajax({
    type: "POST",
    url: "/groups/add_user_to_group",
    data: JSON.stringify(content),
    contentType: "application/json",
    success: function(result){
      $('#modalresponse-body').html(result);
      $('#modalresponse').modal('show');
    }
  });
}


function updateName(){
  group_dic['name'] = $('#modal-group-name').val();
}


function reload(){
  location.reload();
}


