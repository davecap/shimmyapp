# -*- coding: utf-8 -*-
"""
    flaskext.shopify
    ~~~~~~~~~~~~~~~~

    Shopify API extension for Flask.

    See Flask-Shopify documentation for more details.
    
    :copyright: (c) 2011 by David Caplan.
    :license: MIT, see LICENSE for more details.
"""

from flask import request, flash, redirect, url_for, _request_ctx_stack
from functools import wraps

import logging
from pyactiveresource.connection import UnauthorizedAccess

import shopify_api

#from flask.signals import Namespace

# signals = Namespace()
# """Namespace for shopify's signals.
# """

# shop_installed = signals.signal('shop-installed', doc=
# """Signal sent when a registered shop has been installed.
# 
# Actual name: ``shop-installed``
# 
# For example::
# 
#     from flaskext.shopify import shop_installed
# 
#     def welcome():
#         # install the shop
#         shop_installed.send(app)
#         
# """)


def shopify_login_required(func):
    """Requires shopify login credentials (a valid shopify_session)"""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not request.shopify_session:
            return redirect(url_for('index'))
        try:
            return func(*args, **kwargs)
        except UnauthorizedAccess:
            logging.error('Authentication error for site: %s' % request.shopify_session.site)
            flash('Authentication error, please try logging-in again')
            return redirect(url_for('logout'))
    return decorated_view

class Shopify(object):
    
    def __init__(self, app):
        self.app = app
        self.tokengetter_func = None
        self.app.before_request(self.before_request)
    
    def before_request(self):
        """Add the shopify_session to the request if possible.
        If there is no token, shopify_session is set to None.
        """
        if self.app.config['DEBUG']:
            # in debug mode, store the test credentials if possible
            token = (self.app.config['SHOPIFY_TEST_SITE'], self.app.config['SHOPIFY_TEST_PASSWORD'])
            self.app.config['SHOPIFY_API_KEY'] = self.app.config['SHOPIFY_TEST_API_KEY']
        else:
            assert self.tokengetter_func is not None, 'missing tokengetter function'
            token = self.tokengetter_func() # (url, password)
        
        ctx = _request_ctx_stack.top
        
        if token is not None:
            # should be a valid token
            ctx.request.shopify_session = shopify_api.Session(self.app.config['SHOPIFY_API_KEY'], *token)
        else:
            # not logged in, no session created
            ctx.request.shopify_session = None
    
    def install(self, url):
        """Returns a redirect response to the "permission" URL with
        the given shop. This will then prompt the user to install the app
        which will then send them to the welcome view.
        """
        temp_session = shopify_api.Session(self.app.config['SHOPIFY_API_KEY'], url, secret=None, params=None)
        return redirect(temp_session.permission_url())

    def authenticate(self, request):
        """Attempt to authenticate a request.
        The request should contain shop, t, timestamp and signature GET parameters (request.args).
        """
        url = request.args.get('shop')
        return shopify_api.Session(self.app.config['SHOPIFY_API_KEY'], url, self.app.config['SHOPIFY_SHARED_SECRET'], params=request.args)
    
    def tokengetter(self, f):
        """Registers a function as tokengetter.  The tokengetter has to return
        a tuple of ``(url, token)`` with the user's token and token secret.
        If the data is unavailable, the function must return `None`.
        """
        self.tokengetter_func = f
        return f
    
