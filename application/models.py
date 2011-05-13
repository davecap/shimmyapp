"""
models.py

"""

from google.appengine.ext import db

#
# SHIMMY - Models
#

class Shop(db.Model):
    name = db.StringProperty(required=True)
    domain = db.StringProperty(required=True)
    password = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)

class Image(db.Model):
    shop_domain = db.StringProperty(required=True)
    # shop = db.ReferenceProperty(Shop, collection_name='images', required=False)
    product_id = db.IntegerProperty(required=True)
    product_handle = db.StringProperty(required=True)
    filename = db.StringProperty(required=True)
    mimetype = db.StringProperty(required=True)
    image = db.BlobProperty(default=None)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    
