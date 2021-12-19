# -*- coding: utf-8 -*-
# zato: ide-deploy=True

from json import dumps, loads
from bson import json_util
import pytz
from models import *
# các model User, GoogleAccount, OutlookAccount, Contact, SyncContacts
from zato.server.service import Service


class GetUserSyncContacts(Service):
  """ Nhận request gồm accessToken lấy user tương ứng, 
      lấy thông tin danh bạ đã được đồng bộ qua api từ tài khoản liên kết của user
  """

  class SimpleIO:
    input_required = 'accessToken'

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
    
    user = User.objects(user_id = userId)[0]
    syncContacts = user.sync_contacts # object của model SyncContacts

    userContacts = [
      {
        'phoneName': contact.phone_name,
        'phoneNumbers': [
          phoneNumber
          for phoneNumber in contact.phone_numbers
        ]
      }
      for contact in syncContacts.contacts
    ]

    userContacts.sort(key = lambda x: x['phoneName'].lower())

    vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')

    if syncContacts.sync_at is None :
      syncAt = None
    else :
      syncAt = dumps(pytz.utc.localize(syncContacts.sync_at).astimezone(vietnam_tz), default=str)
    
    response.payload = {
      'syncAt': syncAt,
      'contacts': userContacts
    }
    response.status_code = 200