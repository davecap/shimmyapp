#!/usr/bin/env python
# Copyright 2011 Erik Karulf. All Rights Reserved.

import inspect
import new

from pyactiveresource.activeresource import ActiveResource
from pyactiveresource.connection import Connection
from shopify_api import util

def AuthException(Exception):
    pass

def _remote_resources():
    remote = []
    resources = __import__('shopify_api.resources', fromlist=['__all__'])
    for name in dir(resources):
        resource = getattr(resources, name)
        if inspect.isclass(resource) and issubclass(resource, ShopifyResource):
            remote.append(resource)
    return remote


class Countable(object):
    def count(self, **options):
        return self.get('count', **options).get('count')


class ShopifyResource(ActiveResource, Countable):
    pass

class MetafieldResource(object):
    
    def metafields(self):
        return self.session.Metafield.find(resource=self.plural,
                                           resource_id=self.id)

    def add_metafield(self, metafield):
        if not hasattr(self.id):
            raise (ArgumentError, "You can only add metafields to resource"
                                  " that has been saved")

        metafield.prefix_options = {
            'resource': self.plural,
            'resource_id': self.id,
        }

        metafield.save()
        return metafield


class EventResource(object):
    
    def events(self):
        return self.session.Events.find(resource=self.plural,
                                        resource_id=self.id)


# Session must remain at the bottom of the file to ease circular imports
class Session(Connection):
    
    @classmethod
    def prepare_shop_domain(cls, url):
        if not url:
            return None
        else:
            if 'http://' in url:
                url = url.replace('http://','')
            elif 'https://' in url:
                url = url.replace('https://','')
            if '.' not in url:
                # extend url to myshopify.com if no host is given
                url = '%s.myshopify.com' % url
            return url
    
    def permission_url(self):
        return 'http://%s/admin/api/auth?api_key=%s' % (self.url, self.user)
    
    def validate_signature(self, secret, params):
        if 'signature' in params and 't' in params and 'timestamp' in params:
            # TODO: check that timestamp is <= 24 hours ago
            # If the signature checks out, we know the request came from Shopify
            if util.md5(secret+"shop=%st=%stimestamp=%s" % (self.url, params['t'], params['timestamp'])).hexdigest() == params['signature']:
                return True
        return False
    
    def __init__(self, api_key, url, secret, params=None, protocol='https'):
        """init is called in two cases: either with request parameters or without.
        If params are passed, we attempt to authenticate the url/secret combo.
        secret can be either the app's shared_secret or the user's password.
        """
        self.url = Session.prepare_shop_domain(url)
        self.user = api_key
        
        if params is not None:
            # attempt to authenticate the params
            if self.validate_signature(secret, params):
                password = util.md5(secret+params['t']).hexdigest()
            else:
                raise AuthException('Unable to authenticate url: %s' % self.url)
        else:
            password = secret
        
        site = "%s://%s/admin/" % (protocol, self.url)
        super(Session, self).__init__(site, self.user, password)
        
        for resource in _remote_resources():
            name = resource.__name__
            resource_class = new.classobj(name, (resource,), {'_site': site})
            resource_class._connection = resource_class.session = self
            setattr(self, name, resource_class)
        
    
