# -*- coding: utf-8 -*-
# zato: ide-deploy=True

from zato.server.service import Service

class ConfiguringCORS(Service):
  """ Đây là service dùng để xác thực CORS cho các request đến từ trình duyệt
  """

  def handle_OPTIONS(self):
    self.response.headers = {
      'Access-Control-Allow-Origin' : '*',
      'Access-Control-Allow-Headers': '*',
      'Access-Control-Allow-Methods': '*'
    }