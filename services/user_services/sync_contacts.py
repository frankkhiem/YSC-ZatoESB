# -*- coding: utf-8 -*-
# zato: ide-deploy=True

from json import dumps, loads
from bson import json_util
import datetime
from models import *
# các model User, GoogleAccount, OutlookAccount, Contact, SyncContacts
from zato.server.service import Service


class SyncContacts(Service):
  """ Nhận request gồm userId lấy user tương ứng, 
      đồng bộ 2 tập danh bạ google và outlook vào trong sync_contacts
  """

  class SimpleIO:
    input_required = 'userId'

  def handle(self):
    # Khai báo đối tượng request và response của service
    request = self.request.input
    response = self.response

    userId = request['userId']  

    # Load contacts mới nhất từ google và outlook trước khi đồng bộ
    self.invoke('google-schedule.google-schedule', {
      'userId': userId
    })
    self.invoke('outlook-schedule.outlook-schedule', {
      'userId': userId
    })

    user = User.objects(user_id = userId)[0]

    syncContacts = user.sync_contacts # object của model SyncContacts

    if user.google.contacts is not None :
      googleContacts = user.google.contacts

    if user.outlook.contacts is not None :
      outlookContacts = user.outlook.contacts

    # Lọc các danh bạ trùng trên trong list danh bạ
    index = 0
    while index < len(syncContacts.contacts) :
      subIndex = index + 1
      while subIndex < len(syncContacts.contacts) :
        if syncContacts.contacts[subIndex].phone_name == syncContacts.contacts[index].phone_name :
          for phoneNumber in syncContacts.contacts[subIndex].phone_numbers :
            if phoneNumber not in syncContacts.contacts[index].phone_numbers :
              syncContacts.contacts[index].phone_numbers.append((phoneNumber))
          del syncContacts.contacts[subIndex]
          subIndex -= 1
        subIndex += 1
      index += 1

    # Đưa danh bạ google đồng bộ vào danh bạ trong db
    for gg in googleContacts :
      if any(contact.phone_name == gg.phone_name for contact in syncContacts.contacts) :
        for i in range(len(syncContacts.contacts)):
          if syncContacts.contacts[i].phone_name == gg.phone_name:
            for phoneNumber in gg.phone_numbers :
              if phoneNumber not in syncContacts.contacts[i].phone_numbers :
                syncContacts.contacts[i].phone_numbers.append((phoneNumber))
            break
      else :
        newContact = Contact(phone_name=gg.phone_name, phone_numbers=gg.phone_numbers)
        syncContacts.contacts.append(newContact)
    
    # Đưa danh bạ outlook đồng bộ vào danh bạ trong db
    for ol in outlookContacts :
      if any(contact.phone_name == ol.phone_name for contact in syncContacts.contacts) :
        for i in range(len(syncContacts.contacts)):
          if syncContacts.contacts[i].phone_name == ol.phone_name:
            for phoneNumber in ol.phone_numbers :
              if phoneNumber not in syncContacts.contacts[i].phone_numbers :
                syncContacts.contacts[i].phone_numbers.append((phoneNumber))
            break
      else :
        newContact = Contact(phone_name=ol.phone_name, phone_numbers=ol.phone_numbers)
        syncContacts.contacts.append(newContact)

    syncContacts.sync_at = datetime.datetime.now()

    # Lưu lại vào database
    user.save()

    response.payload = {
      'success': True
    }
