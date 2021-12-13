# -*- coding: utf-8 -*-
# zato: ide-deploy=True

from json import dumps, loads
from bson import json_util
import pytz
from models import *
# các model User, GoogleAccount, OutlookAccount, Contact, SyncContacts
from zato.server.service import Service, List


class DeleteMultipleContacts(Service):
  """ Nhận request gồm accessToken lấy user tương ứng, 
      xóa nhiều liên hệ trong danh bạ
  """

  class SimpleIO:
    input_required = 'accessToken', List('listPhoneNames')

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
    contacts = user.sync_contacts.contacts

    for phoneName in request['listPhoneNames'] :
      # self.logger.info(phoneName)
      for i in range(len(contacts)):
        if contacts[i]['phone_name'] == phoneName:
          del contacts[i]
          break
      user.save()

    response.payload = {
      'success': True,
      'message': 'Delete multiple contacts successfully'
    }