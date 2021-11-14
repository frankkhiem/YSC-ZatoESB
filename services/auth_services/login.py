# -*- coding: utf-8 -*-
# zato: ide-deploy=True

from json import dumps, loads
from models import *
# các model User, GoogleAccount, Contact
from zato.server.service import Service, AsIs


class Login(Service):
  """ Nhận request gồm email, password đăng nhập tài khoản người dùng trên firebase.
  """

  class SimpleIO:
    input_required = 'email', AsIs('password')

  def handle(self):
    # Khai báo đối tượng request và response của service
    request = self.request.input
    response = self.response
    # Set headers tránh lỗi CORS
    response.headers = {
      'Access-Control-Allow-Origin' : '*',
    }

    email = request['email']
    password = request['password']

    # Khai báo kết nối tới api đăng nhập firebase
    login_conn = self.outgoing.plain_http['Login Firebase'].conn

    params = {
      'key': 'AIzaSyAq62TOWEIlcCPx6MGslvg8ao33s9v9WLE'
    }
    payload = {
      'email': email,
      'password': password,
      'returnSecureToken': True
    }
    headers = {
      'Content-Type': 'application/json'
    }

    # Gửi request tới firebase đăng nhập tài khoản trả về res_login
    res_login = login_conn.post(self.cid, payload, params, headers=headers)

    if res_login.status_code == 200:
      response.payload = {
        'userId': res_login.data['localId'],
        'accessToken': res_login.data['idToken']
      }
      response.status_code = 200

    else:
      response.payload = {
        'message': res_login.data['error']['message']
      }
      response.status_code = res_login.status_code

    return