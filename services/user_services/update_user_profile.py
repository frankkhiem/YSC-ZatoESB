# -*- coding: utf-8 -*-
# zato: ide-deploy=True

from json import dumps, loads
from bson import json_util
from datetime import datetime
from models import *
# các model User, GoogleAccount, OutlookAccount, Contact, SyncContacts
from zato.server.service import Service


class UpdateUserProfile(Service):
  """ Nhận request gồm accessToken trả về thông tin user
  """

  class SimpleIO:
    input_required = 'accessToken'
    input_optional = 'userName', 'birthday', 'avatar', 'aboutMe'
    default_value = None
 
  def handle(self):
    # Khai báo đối tượng request và response của service
    request = self.request.input
    response = self.response
    # Set headers tránh lỗi CORS
    response.headers = {
      'Access-Control-Allow-Origin' : '*',
    }

    ##############################################################################################
    # Mọi service cần xác thực người dùng và lấy thông tin của người đều cần các dòng trong vùng #
    accessToken = request['accessToken']

    input = {
      'accessToken': accessToken
    }

    # Gọi auth middleware xác thực người dùng thông qua accessToken
    res_auth = self.invoke('auth-middleware.auth-middleware', input)

    if not res_auth['auth']:
      response.payload = {
        'success': False,
        'message': 'Unauthorized'
      }
      response.status_code = 401
      return
    
    else:
      # userId nhận được dùng để query dữ liệu tương ứng với người dùng request đến
      userId = res_auth['userId']
    ##############################################################################################
    
    # Lấy profile từ userId
    # user = User.objects.get(user_id = userId).to_mongo().to_dict() # Convert từ QuerySet sang Dict
    user = User.objects.get(user_id = userId) # Đây là object thuộc class QuerySet

    if request['userName'] is None :
      name = 'Guest'
    else :
      name = request['userName']

    if request['birthday'] is not None :
      try :
        birthday = datetime.strptime(request['birthday'], '%Y-%m-%d')
      except :
        birthday = None
    else :
      birthday = None

    fields = {
      'user_name': name,
      'birthday': birthday,
      'avatar': request['avatar'],
      'about_me': request['aboutMe']
    }

    user.update(**fields)

    response.payload = {
      'success': True,
      'message': 'Update profile successfully'
    }

    response.status_code = 200 
    return