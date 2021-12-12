# -*- coding: utf-8 -*-
# zato: ide-deploy=True

from json import dumps, loads
from bson import json_util
import datetime
from models import *
# các model User, GoogleAccount, OutlookAccount, Contact, SyncContacts
from zato.server.service import Service


class SyncReverseOutlook(Service):
  """ Nhận request gồm userId lấy user tương ứng, 
      đồng bộ ngược từ danh bạ trong db ra outlook contacts
  """

  class SimpleIO:
    input_required = 'userId'

  def handle(self):
    # Khai báo đối tượng request và response của service
    request = self.request.input
    response = self.response

    userId = request['userId']  

    # Load làm mới lại danh bạ Outlook trước khi đồng bộ ngược
    self.invoke('outlook-schedule.outlook-schedule', {
      'userId': userId
    })

    user = User.objects(user_id = userId)[0]

    outlookAccount = user.outlook
    syncContacts = user.sync_contacts

    if not outlookAccount.activated :
      self.logger.info('Outlook chua lien ket')
      response.payload = {
        'success': False,
        'message': 'Outlook account not linked'
      }
      return
    
    self.logger.info('Tien hanh dong bo nguoc Outlook')

    # Hàm update liên hệ Outlook
    def updateOutlookContact(olContact, phoneNumbers) :
      self.logger.info('Update lien he')
      update_contacts_conn = self.outgoing.plain_http['Update Outlook Contact'].conn
      params = {
        'id': olContact.id
      }
      payload = {
        "homePhones": phoneNumbers
      }
      outlookToken = 'Bearer ' + outlookAccount.access_token
      headers = {
        'Content-Type': 'application/json',
        'Authorization': outlookToken
      }
      # Gửi request sửa 1 danh bạ google
      update_contacts_conn.patch(self.cid, payload, params, headers=headers)

    # Hàm delete liên hệ Outlook
    def deleteOutlookContact(olContact) :
      self.logger.info('Delete lien he')
      delete_contacts_conn = self.outgoing.plain_http['Delete Outlook Contact'].conn
      params = {
        'id': olContact.id
      }
      payload = {
        # không có payload body
      }
      outlookToken = 'Bearer ' + outlookAccount.access_token
      headers = {
        'Content-Type': 'application/json',
        'Authorization': outlookToken
      }
      # Gửi request tạo mới 1 danh bạ google
      delete_contacts_conn.delete(self.cid, params, headers=headers)

    # Hàm tạo mới liên hệ trong Outlook
    def createOutlookContact(phoneName, phoneNumbers) :
      self.logger.info('Tao moi lien he')
      create_contacts_conn = self.outgoing.plain_http['Create Outlook Contact'].conn
      params = {
        # không có params
      }
      payload = {
        "givenName": phoneName,
        "homePhones": phoneNumbers
      }
      outlookToken = 'Bearer ' + outlookAccount.access_token
      headers = {
        'Content-Type': 'application/json',
        'Authorization': outlookToken
      }
      # Gửi request tạo mới 1 danh bạ google
      create_contacts_conn.post(self.cid, payload, params, headers=headers)

    # Vòng lặp dùng để update hoặc delete các liên hệ đã có trong google contacts
    for olContact in outlookAccount.contacts :
      if any(olContact.phone_name == contact.phone_name for contact in syncContacts.contacts) :
        # self.logger.info('Update lien he')
        for contact in syncContacts.contacts :
          if contact.phone_name == olContact.phone_name :
            if set(contact.phone_numbers) != set(olContact.phone_numbers) :
              updateOutlookContact(olContact, contact.phone_numbers)
            break
      else :
        deleteOutlookContact(olContact)

    # Vòng lặp dùng để tạo mới các liên hệ chưa có trong google
    for contact in syncContacts.contacts :
      if not any(contact.phone_name == olContact.phone_name for olContact in outlookAccount.contacts) :
        # self.logger.info('Tao moi lien he')
        createOutlookContact(contact.phone_name, contact.phone_numbers)

    # Lưu lại vào database
    user.save()

    response.payload = {
      'success': True
    }

    return
