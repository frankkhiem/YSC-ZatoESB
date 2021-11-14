# -*- coding: utf-8 -*-
# zato: ide-deploy=True

from json import dumps, loads
from bson import json_util
from models import *
# các model User, GoogleAccount, OutlookAccount, Contact, SyncContacts
from zato.server.service import Service


class LoadZaloProfile(Service):
  """ Nhận request gồm accessToken lấy user tương ứng, 
      lấy thông tin tài khoản zalo qua api từ tài khoản liên kết của user
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
    zaloAccount = user.zalo # object của model ZaloAccount

    if not zaloAccount.activated :
      response.payload = {
        'success': False,
        'message': 'Zalo account not linked'
      }
      response.status_code = 400
      return

    res_load_profile = self.loadProfile(zaloAccount.access_token)

    if res_load_profile['data']['error'] == 0 :
      accountName = res_load_profile['data']['name']
      accountAvatar = res_load_profile['data']['picture']['data']['url']
      zaloAccount.account_name = accountName
      zaloAccount.account_avatar = accountAvatar
      user.save()
      response.payload = {
        'success': True,
        'zaloName': accountName,
        'zaloAvatar': accountAvatar
      }
      response.status_code = 200
      return

    elif res_load_profile['data']['error'] != 0 :
      result = self.refreshZaloAccessToken(zaloAccount.refresh_token)
      if result['status'] :
        zaloAccount.access_token = result['access_token'] 
        zaloAccount.refresh_token = result['refresh_token']      
        res_load_profile = self.loadProfile(zaloAccount.access_token)
        accountName = res_load_profile['data']['name']
        accountAvatar = res_load_profile['data']['picture']['data']['url']
        zaloAccount.account_name = accountName
        zaloAccount.account_avatar = accountAvatar
        user.save()
        response.payload = {
          'success': True,
          'zaloName': accountName,
          'zaloAvatar': accountAvatar
        }
        response.status_code = 200
        return

      else :
        zaloAccount.activated = False
        zaloAccount.access_token = None
        zaloAccount.refresh_token = None
        zaloAccount.account_name = None
        zaloAccount.account_avatar= None
        user.save()
        response.payload = {
          'success': False,
          'message': 'Zalo account not linked'
        }
        response.status_code = 400
        return
    
    response.payload = {
      'success': False,
      'message': 'An error has occurred'
    }
    response.status_code = 400


  ############################################

  def loadProfile(self, accessToken):
    load_contacts_conn = self.outgoing.plain_http['Load Zalo Profile'].conn

    params = {
      'fields': 'name, picture'
    }
    payload = {
      # Không có payload trong body
    }

    headers = {
      'Content-Type': 'application/json;charset=utf-8',
      'access_token': accessToken
    }
    # Gửi get request lấy hồ sơ zalo
    res_load_contacts = load_contacts_conn.get(self.cid, params, headers=headers)

    return {
      'status_code': res_load_contacts.status_code,
      'data': res_load_contacts.json()
    }


  def refreshZaloAccessToken(self, refreshToken):
    # Khai báo kết nối tới api trao đổi token của google
    exchange_token_conn = self.outgoing.plain_http['Exchange Zalo Token'].conn

    params = {
      # Không có params
    }
    payload = {
      'app_id': '2399654782955708252',
      'refresh_token': refreshToken,
      'grant_type': 'refresh_token'
    }
    headers = {
      'Content-Type': 'application/x-www-form-urlencoded',
      'secret_key': '9K1qBjgT6BHTZpQ9SwoI'
    }

    res_exchange_token = exchange_token_conn.post(self.cid, payload, params, headers=headers)

    # self.logger.info(res_exchange_token.data)
    # self.logger.info(res_exchange_token.status_code)
    
    self.logger.info('Goi den refresh roi ...............!')

    if 'access_token' in res_exchange_token.json() and 'refresh_token' in res_exchange_token.json():
      return {
        'status': True,
        'access_token': res_exchange_token.json()['access_token'],
        'refresh_token': res_exchange_token.json()['refresh_token']
      }
    else :
      return {
        'status': False
      }
