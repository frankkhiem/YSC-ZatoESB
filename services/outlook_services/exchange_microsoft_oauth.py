# -*- coding: utf-8 -*-
# zato: ide-deploy=True

from json import dumps, loads
from bson import json_util
from models import *
# các model User, GoogleAccount, OutlookAccount, Contact, SyncContacts
from zato.server.service import Service


class ExchangeMicrosoftToken(Service):
  """ Nhận request gồm accessToken lấy user tương ứng, 
      authorization_code từ tài khoản Microsoft của người dùng để trao đổi accessToken, refreshToken 
      truy cập tới API Microsoft tương ứng với người dùng
  """

  class SimpleIO:
    input_required = 'accessToken', 'authorization_code'

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
    outlookAccount = user.outlook # object của model GoogleAccount


    # auth code google người dùng gửi lên
    authorization_code = request['authorization_code']

    # Khai báo kết nối tới api trao đổi token của google
    exchange_token_conn = self.outgoing.plain_http['Exchange Microsoft Token'].conn

    params = {
      # Không có params
    }
    payload = {
      'code': authorization_code,
      'client_id': 'e63fb652-b80d-439f-a487-87dc8ea3bd7b',
      'client_secret': 'ulP7Q~SLIVe3mOgL37e2pROBYusN2CxZehTsK',
      'redirect_uri': 'http://localhost:8080/outlook/get-auth-code',
      'grant_type': 'authorization_code',
      'scope': 'Contacts.Read Contacts.ReadWrite'
    }
    headers = {
      'Content-Type': 'application/x-www-form-urlencoded'
    }

    res_exchange_token = exchange_token_conn.post(self.cid, payload, params, headers=headers)

    # self.logger.info(res_exchange_token.json())

    if res_exchange_token.status_code == 200:
      outlookAccount.access_token = res_exchange_token.json()['access_token']
      outlookAccount.refresh_token = res_exchange_token.json()['refresh_token']
      outlookAccount.activated = True
      user.save()
      response.payload = {
        'message': 'Exchange Microsoft token successfully'
      }
      response.status_code = 200
      return

    response.payload = {
      'message': 'Exchange Microsoft token failed'
    }
    response.status_code = 400