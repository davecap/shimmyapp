"""
models.py

"""

from google.appengine.ext import db

#
# SHIMMY - Models
#

# use shopify_id as the primary key???

class Shop(db.Model):
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    name = db.StringProperty(required=True)
    url = db.StringProperty(required=True)
    logo = db.StringProperty()
    #access_token = db.StringProperty()

# Product
#   shopify_id, shop, sku, title, created_on, modified_on

# Variant
#   shopify_id, shop, product, sku, title, option1, option2, option3

# Image
#   shopify_id, product, variant, filename, remote_url, order

class Upload(db.Model):
    shop_url = db.StringProperty(required=True)
    product_id = db.StringProperty(required=True)
    filename = db.StringProperty(required=True)
    mime_type = db.StringProperty(required=True)
    blob = db.BlobProperty(default=None),
    download_url = db.StringProperty(required=True)
    thumb_url = db.StringProperty(required=False)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)

# class User(db.Model):
#     id = db.StringProperty(required=True)
#     created = db.DateTimeProperty(auto_now_add=True)
#     updated = db.DateTimeProperty(auto_now=True)
#     name = db.StringProperty(required=True)
#     profile_url = db.StringProperty(required=True)
#     picture = db.StringProperty(required=True)
#     location = db.StringProperty()
#     access_token = db.StringProperty()
#     
#     def get_location(self):
#         # TODO: look for UserProfile location data
#         pass
# 
# class UserEvent(db.Model):
#     id = db.StringProperty(required=True)
#     created = db.DateTimeProperty(auto_now_add=True)
#     updated = db.DateTimeProperty(auto_now=True)
#     friend_ids = db.StringListProperty(default=[])
#     event_id = db.StringProperty(default=None)
#     
#     # TODO: async?
#     def add_friend(self, user_id):
#         if user_id not in self.friend_ids:
#             self.friend_ids.append(user_id)
#             self.put()
#     
#     # TODO: async?
#     def remove_friend(self, user_id):
#         if user_id in self.friend_ids:
#             self.friend_ids.remove(user_id)
#             self.put()
#     
# class UserProfile(db.Expando):
#     id = db.StringProperty(required=True)
#     # latitude
#     # longitude
#     # city
#     # country
#     # postal_code
#     # interests = g.get_connections("me", "interests")
#     # music = g.get_connections("me", "music")
#     # books = g.get_connections("me", "books")
#     # movies = g.get_connections("me", "movies")
#     # television = g.get_connections("me", "television")
#     # albums = g.get_connections("me", "albums")
#     # #likes = g.get_connections("me", "likes")
