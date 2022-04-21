# -*- coding: utf-8 -*-
# zato: ide-deploy=True

from json import dumps, loads
from bson import json_util
from models import *
# các model User, GoogleAccount, OutlookAccount, Contact, SyncContacts
from zato.server.service import Service


class GetUserProfile(Service):
  """ Nhận request gồm accessToken trả về thông tin user
  """

  class SimpleIO:
    input = 'accessToken'

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

    # response.payload = loads(json_util.dumps(user)) # Khắc phục lỗi convert ObjectId của mongo sang json
    response.payload = {
      'userId': user['user_id'],
      'userName': user['user_name'],
      'email': user['email'],
      'birthday': user['birthday'],
      'avatar': user['avatar'],
      'aboutMe': user['about_me'],
      'linkedGoogle': user['google']['activated'],
      'linkedOutlook': user['outlook']['activated'],
      'linkedZalo': user['zalo']['activated']
    }

    response.status_code = 200

    return