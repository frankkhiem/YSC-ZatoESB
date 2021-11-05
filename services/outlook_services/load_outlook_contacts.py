# -*- coding: utf-8 -*-
# zato: ide-deploy=True

from json import dumps, loads
from bson import json_util
from models import *
# các model User, GoogleAccount, OutlookAccount, Contact, SyncContacts
from zato.server.service import Service


class LoadOutlookContacts(Service):
  """ Nhận request gồm accessToken lấy user tương ứng, 
      lấy thông tin danh bạ outlook qua api từ tài khoản liên kết của user
  """

  class SimpleIO:
    input = 'accessToken'

  def handle(self):
    # Khai báo đối tượng request và response của service
    request = self.request.input
    response = self.response

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
    outlookAccount = user.outlook # object của model OutlookAccount

    if not outlookAccount.activated :
      response.payload = {
        'success': False,
        'message': 'Outlook account not linked'
      }
      response.status_code = 400
      return

    res_load_contacts = self.loadContacts(outlookAccount.access_token)

    if res_load_contacts['status_code'] == 200 :
      listContacts =  res_load_contacts['data']['value']
      outlookAccount.contacts = self.saveContacts(listContacts)
      user.save()
      response.payload = {
        'success': True,
        'message': 'Load and save Outlook contacts successfully' 
      }
      response.status_code = 200
      return

    elif res_load_contacts['status_code'] == 401 :
      result = self.refreshMicrosoftAccessToken(outlookAccount.refresh_token)
      if result['status'] :
        outlookAccount.access_token = result['access_token']       
        res_load_contacts = self.loadContacts(outlookAccount.access_token)
        listContacts = res_load_contacts['data']['value']
        outlookAccount.contacts = self.saveContacts(listContacts)
        user.save()
        response.payload = {
          'success': True,
          'message': 'Load and save Outlook contacts successfully'
        }
        response.status_code = 200
        return

      else :
        outlookAccount.activated = False
        outlookAccount.access_token = None
        outlookAccount.refresh_token = None
        user.save()
        response.payload = {
          'success': False,
          'message': 'Outlook account not linked'
        }
        response.status_code = 400
        return
    
    response.payload = {
      'success': False,
      'message': 'An error has occurred'
    }
    response.status_code = 400


  ############################################

  def loadContacts(self, accessToken):
    load_contacts_conn = self.out.rest['Load Outlook Contacts'].conn

    params = {
      # Không có params
    }
    payload = {
      # Không có payload trong body
    }

    microsoftToken = 'Bearer ' + accessToken
    headers = {
      'Content-Type': 'application/json',
      'Authorization': microsoftToken
    }
    # Gửi get request lấy danh bạ outlook
    res_load_contacts = load_contacts_conn.get(self.cid, params, headers=headers)
    # self.logger.info(type(res_load_contacts.data['value']))

    return {
      'status_code': res_load_contacts.status_code,
      'data': res_load_contacts.data
    }


  def refreshMicrosoftAccessToken(self, refreshToken):
    # Khai báo kết nối tới api trao đổi token của microsoft
    exchange_token_conn = self.out.rest['Exchange Microsoft Token'].conn

    params = {
      # Không có params
    }
    payload = {
      'refresh_token': refreshToken,
      'client_id': 'e63fb652-b80d-439f-a487-87dc8ea3bd7b',
      'client_secret': 'ulP7Q~SLIVe3mOgL37e2pROBYusN2CxZehTsK',
      'redirect_uri': 'http://localhost:3000/google-callback',
      'grant_type': 'refresh_token',
      'scope': 'Contacts.Read Contacts.ReadWrite'
    }
    headers = {
      'Content-Type': 'application/x-www-form-urlencoded'
    }

    res_exchange_token = exchange_token_conn.post(self.cid, payload, params, headers=headers)

    # self.logger.info(res_exchange_token.data)
    # self.logger.info(res_exchange_token.status_code)
    
    self.logger.info('Goi den refresh roi ...............!')

    if res_exchange_token.status_code == 200 :
      return {
        'status': True,
        'access_token': res_exchange_token.data['access_token']
      }
    else :
      return {
        'status': False
      }
    
  
  def saveContacts(self, dataContacts):
    contacts = []
    for item in dataContacts :
      phoneName = item['displayName']
      phoneNumbers = []
      for phoneNumber in item['phones'] :
        phoneNumbers.append(phoneNumber['number'])
      # self.logger.info(phoneName)
      # self.logger.info(phoneNumbers)
      contact = Contact(phone_name=phoneName, phone_numbers=phoneNumbers)
      contacts.append(contact)

    return contacts
