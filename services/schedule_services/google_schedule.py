# -*- coding: utf-8 -*-
# zato: ide-deploy=True

from json import dumps, loads
from bson import json_util
from models import *
# các model User, GoogleAccount, OutlookAccount, Contact, SyncContacts
from zato.server.service import Service


class GoogleSchedule(Service):
  """ Nhận userId load google contacts của người dùng tương ứng
  """

  class SimpleIO:
    input_required = 'userId'

  def handle(self):
    # Khai báo đối tượng request và response của service
    request = self.request.input
    response = self.response
    # Set headers tránh lỗi CORS
    response.headers = {
      'Access-Control-Allow-Origin' : '*',
    }

    userId = request['userId']
    
    user = User.objects(user_id = userId)[0]
    googleAccount = user.google # object của model GoogleAccount

    if not googleAccount.activated :
      response.payload = {
        'success': False,
        'message': 'Google account not linked'
      }
      response.status_code = 400
      return

    res_load_contacts = self.loadContacts(googleAccount.access_token)

    if res_load_contacts['status_code'] == 200 :
      if res_load_contacts['data'] :
        listContacts =  res_load_contacts['data']['connections']
        googleAccount.contacts = self.saveContacts(listContacts)
      else :
        googleAccount.contacts = []
      user.save()
      response.payload = {
        'success': True,
        'message': 'Load and save Google contacts successfully'
      }
      response.status_code = 200
      return

    elif res_load_contacts['status_code'] == 401 :
      result = self.refreshGoogleAccessToken(googleAccount.refresh_token)
      if result['status'] :
        googleAccount.access_token = result['access_token']       
        res_load_contacts = self.loadContacts(googleAccount.access_token)
        if res_load_contacts['data'] :
          listContacts =  res_load_contacts['data']['connections']
          googleAccount.contacts = self.saveContacts(listContacts)
        else :
          googleAccount.contacts = []
        user.save()
        response.payload = {
          'success': True,
          'message': 'Load and save Google contacts successfully'
        }
        response.status_code = 200
        return

      else :
        googleAccount.activated = False
        googleAccount.access_token = None
        googleAccount.refresh_token = None
        user.save()
        response.payload = {
          'success': False,
          'message': 'Google account not linked'
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
    load_contacts_conn = self.outgoing.plain_http['Load Google Contacts'].conn

    params = {
      'personFields': 'names,phoneNumbers'
    }
    payload = {
      # Không có payload trong body
    }

    googleToken = 'Bearer ' + accessToken
    headers = {
      'Content-Type': 'application/json',
      'Authorization': googleToken
    }
    # Gửi get request lấy danh bạ google
    res_load_contacts = load_contacts_conn.get(self.cid, params, headers=headers)

    return {
      'status_code': res_load_contacts.status_code,
      'data': res_load_contacts.json()
    }


  def refreshGoogleAccessToken(self, refreshToken):
    # Khai báo kết nối tới api trao đổi token của google
    exchange_token_conn = self.outgoing.plain_http['Exchange Google Token'].conn

    params = {
      # Không có params
    }
    payload = {
      'client_id': '301608552892-g7inqpodo0dkvlvkmnaqrmpgf8oi695d.apps.googleusercontent.com',
      'client_secret': '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',
      'refresh_token': refreshToken,
      'grant_type': 'refresh_token'
    }
    headers = {
      'Content-Type': 'application/json'
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
      resourceName = item['resourceName']
      etag = item['etag']
      phoneName = item['names'][0]['displayName']
      phoneNumbers = []
      for phoneNumber in item['phoneNumbers'] :
        phoneNumbers.append(phoneNumber['value'])
      contact = GoogleContact(resource_name=resourceName, etag=etag, phone_name=phoneName, phone_numbers=phoneNumbers)
      contacts.append(contact)
    
    return contacts
