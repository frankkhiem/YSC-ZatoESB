# -*- coding: utf-8 -*-
# zato: ide-deploy=True

from json import dumps, loads
from bson import json_util
from models import *
# các model User, GoogleAccount, OutlookAccount, Contact, SyncContacts
from zato.server.service import Service


class ExchangeGoogleToken(Service):
  """ Nhận request gồm accessToken lấy user tương ứng, 
      authorization_code từ tài khoản Google của người dùng để trao đổi accessToken, refreshToken 
      truy cập tới API Google tương ứng với người dùng
  """

  class SimpleIO:
    input = 'accessToken', 'authorization_code'

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
    googleAccount = user.google # object của model GoogleAccount


    # auth code google người dùng gửi lên
    authorization_code = request['authorization_code']

    # Khai báo kết nối tới api trao đổi token của google
    exchange_token_conn = self.out.rest['Exchange Google Token'].conn

    params = {
      # Không có params
    }
    payload = {
      'code': authorization_code,
      'client_id': '301608552892-g7inqpodo0dkvlvkmnaqrmpgf8oi695d.apps.googleusercontent.com',
      'client_secret': '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',
      'redirect_uri': 'http://localhost:8080',
      'grant_type': 'authorization_code'
    }
    headers = {
      'Content-Type': 'application/json'
    }

    res_exchange_token = exchange_token_conn.post(self.cid, payload, params, headers=headers)

    # self.logger.info(res_exchange_token.status_code)

    if res_exchange_token.status_code == 200:
      googleAccount.access_token = res_exchange_token.data['access_token']
      googleAccount.refresh_token = res_exchange_token.data['refresh_token']
      googleAccount.activated = True
      user.save()
      response.payload = {
        'message': 'Exchange Google token successfully'
      }
      response.status_code = 200
      return

    response.payload = {
      'message': 'Exchange Google token failed'
    }
    response.status_code = 400
