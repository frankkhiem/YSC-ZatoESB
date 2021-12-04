# -*- coding: utf-8 -*-
# zato: ide-deploy=True

from json import dumps, loads
from bson import json_util
import pytz
from models import *
# các model User, GoogleAccount, OutlookAccount, Contact, SyncContacts
from zato.server.service import Service, List


class CreateContact(Service):
  """ Nhận request gồm accessToken lấy user tương ứng, 
      tạo mới một liên hệ trong danh bạ
  """

  class SimpleIO:
    input_required = 'accessToken', 'phoneName', List('phoneNumbers')

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

    if not any(contact['phone_name'] == request['phoneName'] for contact in user.sync_contacts.contacts):
      # self.logger.info('Khong co danh ba nao trung ten')
      newContact = Contact()
      newContact.phone_name = request['phoneName']
      newContact.phone_numbers = request['phoneNumbers']

      user.sync_contacts.contacts.append(newContact)
      user.save()

      response.payload = {
        'success': True,
        'message': 'Create new contact successfully',
      }
    else :
      # self.logger.info('Da ton tai danh ba')
      response.payload = {
        'success': False,
        'message': 'Contact already exists',
      }