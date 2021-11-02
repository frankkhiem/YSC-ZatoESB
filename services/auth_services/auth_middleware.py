# -*- coding: utf-8 -*-
# zato: ide-deploy=True

from json import dumps, loads
from models import *
# các model User, GoogleAccount, Contact
from zato.server.service import Service


class AuthMiddleware(Service):
  """ Nhận request gồm accessToken xác thực và trả lại thông tin người dùng tương ứng
  """

  class SimpleIO:
    input = 'accessToken'

  def handle(self):
    # Khai báo đối tượng request và response của service
    request = self.request.input
    response = self.response

    accessToken = request['accessToken']

    # Khai báo kết nối tới api xác thực người dùng từ accessToken của firebase
    auth_conn = self.out.rest['Auth Firebase By AccessToken'].conn

    params = {
      'key': 'AIzaSyAq62TOWEIlcCPx6MGslvg8ao33s9v9WLE'
    }
    payload = {
      'idToken': accessToken
    }
    headers = {
      'Content-Type': 'application/json'
    }

    # Gửi request tới firebase xác thực người dùng trả về res_auth
    res_auth = auth_conn.post(self.cid, payload, params, headers=headers)

    if res_auth.status_code == 200:
      response.payload = {
        'auth': True,
        'userId': res_auth.data['users'][0]['localId']
      }
      response.status_code = 200

    else:
      response.payload = {
        'auth': False,
        'message': 'Unauthorized'
      }
      response.status_code = res_auth.status_code

    return