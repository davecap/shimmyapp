"""
Flask Module Docs:  http://flask.pocoo.org/docs/api/#flask.Module

This file is used for both the routing and logic of your
application.
"""

from flask import url_for, render_template, request, redirect, flash, session, jsonify
from werkzeug import parse_options_header
from werkzeug.exceptions import BadRequest
import logging

from application import app, shopify
from flaskext.shopify import shopify_login_required

from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api.images import get_serving_url

from application.models import Upload

@app.route('/_ah/warmup')
def warmup():
    return ''

@app.route('/')
def index():
    if 'shop' in request.args and request.args.get('shop'):
        # if there is a valid shop GET parameter, this will redirect the user to the "permission url"
        # this will then prompt the user to install the app which will then send them to the welcome view.
        return shopify.install(request.args.get('shop'))
    elif request.shopify_session is None:
        # not logged in, show signup form
        return render_template('install.html')
    else:
        # app code starts here
        shop = request.shopify_session.Shop.current().to_dict()
        products = [ p.to_dict() for p in request.shopify_session.Product.find(limit=10) ]
        return render_template('index.html', shop=shop, products=products)

@app.route('/welcome')
def welcome():
    """Welcome view after a user has installed this app from the App Store.
    This view authenticates their shop and sets up a session.

    see: http://api.shopify.com/authentication.html

    Expects GET parameters: shop, t, timestamp, signature.

    """

    # if they are logged-in already, redirect them
    if request.shopify_session:
        return redirect(url_for('index'))

    # create a session if possible
    try:
        shopify_session = shopify.authenticate(request)
    except Exception, e:
        logging.error('Could not create a session: %s' % str(e))
        flash('Sorry, we couldn\'t log you in.')
        return redirect(url_for('index'))
    else:
        # TODO: get the shop info and set in DB if it isn't already
        session['shopify_token'] = (shopify_session.url, shopify_session.password)
        flash('You are now logged in')
        return redirect(url_for('index'))

@app.route('/logout')
@shopify_login_required
def logout():
    session.pop('shopify_token', None)
    flash('You were signed out')
    return redirect(request.referrer or url_for('index'))

@app.route('/uninstall')
def uninstall():
    """
    Uninstall is called only as a WebHook from Shopify

    """

    # TODO: can I put this in the Shopify extension?

    # If not HTTP_X_SHOPIFY_SHOP_ID -> BadRequest()
    try:
        shop_id = request.headers.get('HTTP_X_SHOPIFY_SHOP_ID', type=int)
    except:
        raise BadRequest()
    else:
        # this request probably came from shopify
        logging.info('Uninstall request for shop ID %d from %s' % (shop_id, request.headers.get('Host')))
        # TODO: set DB flags
        # TODO: session in DB?
        return 'SHOP %d UNINSTALLED OK' % shop_id

# def install_shop(s=None):
#     """
#     Set up a new shop
#     """
#     if not s:
#         s = _shopify_session()
# 
#     # Create a webhook for app removal
#     # Note: this webhook should get automatically deleted from the shop on uninstall
#     d = {   "webhook": {
#                 "address": "http://%s/uninstall" % app.config['SHOPIFY_APP_SITE'],
#                 "format": "json",
#                 "topic": "app/uninstalled"
#             }
#         }
#     res = s.WebHook('/admin/webhooks.json', d)

@app.after_request
def add_header(response):
    """Add header to force latest IE rendering engine and Chrome Frame."""
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    return response

## Error handlers
# Handle 404 errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Handle 500 errors
@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

@shopify.tokengetter
def get_shopify_token():
    """This function is used by the Shopify API extension to get the shop/token pair.
    For now, we store the Shopify shop and password in the session.
    It can also be stored in the DB.

    """
    if 'shopify_token' in session:
        return session['shopify_token']
    else:
        return None


@app.route('/product/<int:product_id>')
@shopify_login_required
def product(product_id):
    shop = request.shopify_session.Shop.current().to_dict()
    product = request.shopify_session.Product.find(product_id).to_dict()
    return render_template('product.html', shop=shop, product=product)


@app.route('/+upload', methods=['GET', 'POST'])
@shopify_login_required
def upload():
    # if request.method == 'GET':
    #     # we are expected to return a list of dicts with infos about the already available files:
    #     file_infos = []
    #     for file_name in list_files():
    #         file_url = url_for('download', file_name=file_name)
    #         file_size = get_file_size(file_name)
    #         file_infos.append(dict(name=file_name,
    #                                size=file_size,
    #                                url=file_url))
    #     return jsonify(files=file_infos)
    if request.method == 'POST':
        # we are expected to save the uploaded file and return some infos about it:
        data_file = request.files.get('data_file')
        file_name = data_file.filename
        header = data_file.headers['Content-Type']
        blob_key = blobstore.BlobKey(parse_options_header(header)[1]['blob-key'])
        blob = blobstore.BlobInfo.get(blob_key)
        file_size = len(blob)
        download_url = get_serving_url(blob_key)
        thumb_url = get_serving_url(blob_key, size=250)
        # create a new Upload object
        upload = Upload(shop_url=request.shopify_session.url,
                        product_id=request.form['product_id'],
                        filename = blob.filename,
                        mime_type = blob.content_type,
                        blob = blob,
                        download_url = download_url,
                        thumb_url = thumb_url
                        )
        upload.put()
        return jsonify(name=file_name, size=file_size, url=download_url, thumbnail=thumb_url)
    else:
        return render_template('500.html'), 500

@app.route('/preupload', methods=['GET','POST'])
@shopify_login_required
def preupload():
    upload_url = blobstore.create_upload_url(url_for('upload'))
    logging.info('Preupload requested: %s' % upload_url)
    if request.is_xhr:
        return upload_url
    else:
        return render_template('500.html'), 500
