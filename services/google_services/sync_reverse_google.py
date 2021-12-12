# -*- coding: utf-8 -*-
# zato: ide-deploy=True

from json import dumps, loads
from bson import json_util
import datetime
from models import *
# các model User, GoogleAccount, OutlookAccount, Contact, SyncContacts
from zato.server.service import Service


class SyncReverseGoogle(Service):
  """ Nhận request gồm userId lấy user tương ứng, 
      đồng bộ ngược từ danh bạ trong db ra google contacts
  """

  class SimpleIO:
    input_required = 'userId'

  def handle(self):
    # Khai báo đối tượng request và response của service
    request = self.request.input
    response = self.response

    userId = request['userId'] 
    
    # Load làm mới lại danh bạ Google trước khi đồng bộ ngược
    self.invoke('google-schedule.google-schedule', {
      'userId': userId
    }) 

    user = User.objects(user_id = userId)[0]

    googleAccount = user.google
    syncContacts = user.sync_contacts

    if not googleAccount.activated :
      self.logger.info('Google chua lien ket')
      response.payload = {
        'success': False,
        'message': 'Google account not linked'
      }
      return
    
    self.logger.info('Tien hanh dong bo nguoc Google')

    # Hàm update liên hệ Google
    def updateGoogleContact(ggContact, phoneNumbers) :
      self.logger.info('Update lien he')
      update_contacts_conn = self.outgoing.plain_http['Update Google Contact'].conn
      params = {
        'resourceName': ggContact.resource_name,
        'updatePersonFields': 'phoneNumbers'
      }
      payload = {
        "etag": ggContact.etag,
        "phoneNumbers": [
          {
            "value": phoneNumber
          }
          for phoneNumber in phoneNumbers
        ]
      }
      googleToken = 'Bearer ' + googleAccount.access_token
      headers = {
        'Content-Type': 'application/json',
        'Authorization': googleToken
      }
      # Gửi request sửa 1 danh bạ google
      update_contacts_conn.patch(self.cid, payload, params, headers=headers)

    # Hàm delete liên hệ Google
    def deleteGoogleContact(ggContact) :
      self.logger.info('Delete lien he')
      delete_contacts_conn = self.outgoing.plain_http['Delete Google Contact'].conn
      params = {
        'resourceName': ggContact.resource_name
      }
      payload = {
        # không có payload body
      }
      googleToken = 'Bearer ' + googleAccount.access_token
      headers = {
        'Content-Type': 'application/json',
        'Authorization': googleToken
      }
      # Gửi request tạo mới 1 danh bạ google
      delete_contacts_conn.delete(self.cid, params, headers=headers)

    # Hàm tạo mới liên hệ trong Google
    def createGoogleContact(phoneName, phoneNumbers) :
      self.logger.info('Tao moi lien he')
      create_contacts_conn = self.outgoing.plain_http['Create Google Contact'].conn
      params = {
        'personFields': 'names,phoneNumbers'
      }
      payload = {
        "names": [
          {
            "givenName": phoneName
          }
        ],
        "phoneNumbers": [
          {
            "value": phoneNumber
          }
          for phoneNumber in phoneNumbers
        ]
      }
      googleToken = 'Bearer ' + googleAccount.access_token
      headers = {
        'Content-Type': 'application/json',
        'Authorization': googleToken
      }
      # Gửi request tạo mới 1 danh bạ google
      create_contacts_conn.post(self.cid, payload, params, headers=headers)

    # Vòng lặp dùng để update hoặc delete các liên hệ đã có trong google contacts
    for ggContact in googleAccount.contacts :
      if any(ggContact.phone_name == contact.phone_name for contact in syncContacts.contacts) :
        # self.logger.info('Update lien he')
        for contact in syncContacts.contacts :
          if contact.phone_name == ggContact.phone_name :
            if set(contact.phone_numbers) != set(ggContact.phone_numbers) :
              updateGoogleContact(ggContact, contact.phone_numbers)
            break
      else :
        deleteGoogleContact(ggContact)

    # Vòng lặp dùng để tạo mới các liên hệ chưa có trong google
    for contact in syncContacts.contacts :
      if not any(contact.phone_name == ggContact.phone_name for ggContact in googleAccount.contacts) :
        # self.logger.info('Tao moi lien he')
        createGoogleContact(contact.phone_name, contact.phone_numbers)

    # Lưu lại vào database
    user.save()

    response.payload = {
      'success': True
    }
    
    return
