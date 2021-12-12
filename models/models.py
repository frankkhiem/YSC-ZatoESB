from mongoengine import *

connect(host="mongodb+srv://user01:user01_password@cluster0.lb6ux.mongodb.net/your_sync_contacts?retryWrites=true&w=majority")

class Contact(EmbeddedDocument):
  phone_name = StringField(max_length=100)
  phone_numbers = ListField(StringField())

class GoogleContact(EmbeddedDocument):
  resource_name = StringField(max_length=100)
  etag = StringField(max_length=100)
  phone_name = StringField(max_length=100)
  phone_numbers = ListField(StringField())

class OutlookContact(EmbeddedDocument):
  id = StringField(max_length=1000)
  phone_name = StringField(max_length=100)
  phone_numbers = ListField(StringField())

class GoogleAccount(EmbeddedDocument):
  activated = BooleanField(required=True, default=False)
  access_token = StringField()
  refresh_token = StringField()
  contacts = ListField(EmbeddedDocumentField(GoogleContact))

class OutlookAccount(EmbeddedDocument):
  activated = BooleanField(required=True, default=False)
  access_token = StringField()
  refresh_token = StringField()
  contacts = ListField(EmbeddedDocumentField(OutlookContact))

class ZaloAccount(EmbeddedDocument):
  activated = BooleanField(required=True, default=False)
  access_token = StringField()
  refresh_token = StringField()
  account_name = StringField()
  account_avatar = StringField()

class SyncContacts(EmbeddedDocument):
  contacts = ListField(EmbeddedDocumentField(Contact))
  sync_at = DateTimeField()

class User(Document):
  user_id = StringField(required=True, unique=True)
  user_name = StringField(max_length=200, required=True)
  email = StringField(required=True, unique=True)
  birthday = DateTimeField()
  avatar = URLField()
  about_me = StringField()
  google = EmbeddedDocumentField(GoogleAccount)
  outlook = EmbeddedDocumentField(OutlookAccount)
  zalo = EmbeddedDocumentField(ZaloAccount)
  sync_contacts = EmbeddedDocumentField(SyncContacts)
  
  meta = {
    'collection': 'user_data'
  }