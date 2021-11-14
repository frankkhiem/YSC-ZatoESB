# -*- coding: utf-8 -*-
# zato: ide-deploy=True

from json import dumps, loads
from models import *
# các model User, GoogleAccount, Contact
from zato.server.service import Service, AsIs


class SignUpFirebase(Service):
  """ Nhận request gồm username, email, password đăng ký tài khoản người dùng trên firebase.
  """

  class SimpleIO:
    input_required = 'username', 'email', AsIs('password')
    # output = 'username', 'email', 'password'

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

    # Khai báo kết nối tới api đăng ký firebase
    signup_conn = self.outgoing.plain_http['Sign up Firebase'].conn

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

    # Gửi thông tin đăng ký tài khoản lên firebase
    res_signup = signup_conn.post(self.cid, payload, params, headers=headers)
    # res_signup có các thuộc tính data (hoặc thay bằng json()), headers, status_code, request

    # self.logger.info('ma trang thai la: {}'.format(type(res_signup.json())))

    if res_signup.status_code == 200:
      response.payload = self.createUser(res_signup.data)
      response.status_code = 200

    else:
      response.payload = {
        'message': res_signup.data['error']['message']
      }
      response.status_code = res_signup.status_code

    return
    # trả response về nơi gọi service
    # response.payload = {
    #   'username': username,
    #   'email': email,
    #   'password': password
    # }

##############################################################

  def createUser(self, data):
    newUser = User()
    newUser.user_id = data['localId']
    newUser.user_name = self.request.input['username']
    newUser.email = data['email']
    newUser.google = GoogleAccount()
    newUser.outlook = OutlookAccount()
    newUser.zalo = ZaloAccount()
    newUser.sync_contacts = SyncContacts()

    newUser.save()
    return {
      'userId': newUser.user_id,
      'username': newUser.user_name,
      'email': newUser.email,
      'accessToken': data['idToken']
    }

