# -*- coding: utf-8 -*-
# zato: ide-deploy=True

from json import dumps, loads
from bson import json_util
import datetime
from models import *
# các model User, GoogleAccount, OutlookAccount, Contact, SyncContacts
from zato.server.service import Service


class SyncContacts(Service):
  """ Nhận input gồm userId lấy user tương ứng, 
      đồng bộ 2 tập danh bạ google và outlook vào trong sync_contacts
  """

  class SimpleIO:
    input = 'userId'

  def handle(self):
    # Khai báo đối tượng request và response của service
    request = self.request.input
    response = self.response

    userId = request['userId']

    user = User.objects(user_id = userId)[0]

    syncContacts = user.sync_contacts # object của model SyncContacts

    googleContacts = user.google.contacts

    outlookContacts = user.outlook.contacts

    # List lưu danh bạ sau khi tiến hành đồng bộ
    syncContacts.contacts = googleContacts + outlookContacts

    syncContacts.sync_at = datetime.datetime.now()

    # Lưu lại vào database
    user.save()

    response.payload = {
      'success': True
    }

    # Cần phải sửa lại phần này