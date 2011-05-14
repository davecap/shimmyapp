"""
models.py

"""

from google.appengine.ext import db
import datetime

from google.appengine.api import memcache

# Custom Properties

# from django.utils import simplejson
# import cPickle as pickle
# 
# class JsonProperty(db.TextProperty):
#     def validate(self, value):
#         return value
# 
#     def get_value_for_datastore(self, model_instance):
#         result = super(JsonProperty, self).get_value_for_datastore(model_instance)
#         result = simplejson.dumps(result)
#         return db.Text(result)
# 
#     def make_value_from_datastore(self, value):
#         try:
#             value = simplejson.loads(str(value))
#         except:
#             pass
#         return super(JsonProperty, self).make_value_from_datastore(value)
# 
# 
# # Use this property to store objects.
# class ObjectProperty(db.BlobProperty):
#     def validate(self, value):
#         try:
#             result = pickle.dumps(value)
#             return value
#         except pickle.PicklingError, e:
#             return super(ObjectProperty, self).validate(value)
# 
#     def get_value_for_datastore(self, model_instance):
#         result = super(ObjectProperty, self).get_value_for_datastore(model_instance)
#         result = pickle.dumps(result)
#         return db.Blob(result)
# 
#     def make_value_from_datastore(self, value):
#         try:
#             value = pickle.loads(str(value))
#         except:
#             pass
#         return super(ObjectProperty, self).make_value_from_datastore(value)

#
# SHIMMY - Models
#

class Shop(db.Model):
    domain = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    
    def cache_key(self):
        return "Shop:%s" % self.key()
    
    def __getattr__(self, name):
        return self.data()[name]
    
    def data(self, shopify_session=None, force=False):
        shop_data = memcache.get(self.cache_key())
        if not force and shop_data is not None:
            return shop_data
        else:
            if shopify_session is not None:
                self.shopify_session = shopify_session
            if not self.shopify_session:
                logging.error("No shopify_session in Shop object")
                return None
            else:
                shop_data = self.shopify_session.Shop.current().to_dict()
                if not memcache.add(self.cache_key(), shop_data, 60*10):
                    logging.error("Memcache set failed for shop data")
                return shop_data
        

class Image(db.Model):
    shop = db.ReferenceProperty(Shop, collection_name='images', required=False)
    product_id = db.IntegerProperty(required=True)
    product_handle = db.StringProperty(required=True)
    image = db.BlobProperty(default=None)
    filename = db.StringProperty(required=True)
    mimetype = db.StringProperty(required=True)
    extension = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    
