# -*- coding: utf-8 -*-
# zato: ide-deploy=True

from json import dumps, loads
from bson import json_util
import pytz
from models import *
# các model User, GoogleAccount, OutlookAccount, Contact, SyncContacts
from zato.server.service import Service


class SyncContactsSchedule(Service):
  """ Lập lịch gọi service sync_contacts đồng bộ tất cả danh bạ của các người dùng
  """

  def handle(self):
    self.logger.info('Goi lap lich dong bo danh ba tat ca nguoi dung')
    users = User.objects
    for user in users:      
      self.invoke('sync-contacts.sync-contacts', {
        'userId': user.user_id
      })