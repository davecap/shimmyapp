"""
Flask Module Docs:  http://flask.pocoo.org/docs/api/#flask.Module

This file is used for both the routing and logic of your
application.
"""
from google.appengine.api import taskqueue, channel
from django.utils import simplejson
from django.template.defaultfilters import slugify

from flask import url_for, render_template, request, redirect, flash, session, make_response, _request_ctx_stack
from werkzeug.exceptions import BadRequest
import logging
import os

from flaskext.shopify import shopify_login_required

from application import app, shopify, models

def get_or_create_shop(shopify_session):        
    shop = models.Shop.all().filter("domain =", shopify_session.url)
    if shop.count() == 0:
        logging.error('No Shop found in DB but shopify_session exists, creating shop')
        shop = models.Shop(domain=shopify_session.url, password=shopify_session.password)
        shop.put()
    else:
        shop = shop[0]
    shop.shopify_session = shopify_session
    return shop

@app.route('/_ah/warmup')
def warmup():
    return ''

@app.before_request
def before_request():
    """ Get the shop data before each request, if possible """
    ctx = _request_ctx_stack.top

@app.after_request
def add_header(response):
    """Add header to force latest IE rendering engine and Chrome Frame."""
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    return response

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
        shop = get_or_create_shop(request.shopify_session)
        # TODO: get more than 250 products
        channel_token = channel.create_channel(request.shopify_session.url)
        products = [ p.to_dict() for p in request.shopify_session.Product.find(limit=250) ]
        vendors = []
        product_types = []
        for p in products:
            p['vendor_slug'] = slugify(p['vendor'])
            p['product_type_slug'] = slugify(p['product_type'])
            vendors.append(p['vendor'])
            product_types.append(p['product_type'])
        vendors = [ { 'slug': slugify(v), 'name': v } for v in set(vendors) ]
        product_types = [ { 'slug': slugify(t), 'name': t } for t in set(product_types) ]
        
        template_values = { 'shop': shop,
                            'vendors': vendors,
                            'product_types': product_types,
                            'products': products,
                            'channel_token': channel_token
                            }
        return render_template('index.html', **template_values)

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

# @shopify_login_required
# @app.route('/product/<int:product_id>', methods=['POST', 'GET'])
# def product(product_id):
#     shop = request.shop
#     product = request.shopify_session.Product.find(product_id).to_dict()
#     images = models.Image.all().filter("shop_domain =", shop.domain).filter("product_id =", product_id)
#     upload_images = [ url_for_image(i) for i in images ]
#     return render_template('product.html', shop=shop, product=product, upload_images=upload_images)

@shopify_login_required
@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        f = request.files['file']
        product_id = int(request.form['product_id'])
        # create a new Image object
        image = models.Image(  shop = get_or_create_shop(request.shopify_session),
                        product_id = product_id,
                        product_handle = request.form['product_handle'],
                        image = f.stream.read(),
                        mimetype = f.content_type,
                        filename = f.filename,
                        extension = os.path.splitext(f.filename)[1]
                    )
        image.put()
        taskqueue.add(url='/tasks/sync', params={'shop_domain': request.shopify_session.url, 'product_id': product_id, 'image_key': image.key()})
        return ''
    else:
        return render_template('500.html'), 500

@app.route('/i/<int:key_id>/<string:filename>')
def image(key_id, filename):
    # NOTE: may be IMPLEMENTED IN WEBAPP TO OVERRIDE HEAD REQUESTS
    i = models.Image.get_by_id(key_id)
    if i:
        response = make_response(i.image)
        response.headers['Content-Type'] = i.mimetype
        return response
    else:
        render_template('404.html'), 404

def url_for_image(i):
    filename = i.product_handle + '-%d%s' % (i.key().id(), i.extension)
    return 'http://' + app.config['SERVER_NAME'] + url_for('image', key_id=i.key().id(), filename=filename)

def allowed_file(filename): 
    """Check to make sure the file is an image.""" 
    allowed_extensions = ['jpg', 'jpeg', 'gif', 'png'] 
    return filename.rsplit('.', 1)[1].lower() in allowed_extensions

# TASKS

@app.route('/tasks/sync', methods=['POST'])
def sync_worker():
    import shopify_api
    def txn():
        # expects: shop_domain, product_id, image_key
        # TODO: replace with shop object key
        shop_domain = request.form.get('shop_domain')
        product_id = int(request.form.get('product_id'))
        image_key = request.form.get('image_key')
        
        if request.shopify_session:
            shopify_session = request.shopify_session
        else:
            dbshop = models.Shop.all().filter("domain =", shop_domain)[0]
            token = (dbshop.domain, dbshop.password)
            shopify_session = shopify_api.Session(app.config['SHOPIFY_API_KEY'], *token)
        
        product = shopify_session.Product.find(product_id) # get the Product fresh from Shopify
        image = models.Image.get(image_key) # get the Image object from the DB
        url = url_for_image(image) # get the URL for the Image data (image view)
        product.images.append({ "src": url }) # add the new image to the images attribute
        
        if not product.save():
            logging.error('Error saving product (%d) images (%s) to Shopify! \n%s' % (product_id, url, str(product.errors.full_messages())))
        else:
            channel.send_message(shopify_session.url, simplejson.dumps({ 'product_id': product_id, 'image_urls': [ i.src for i in product.images ] }))
            logging.info('Product image (%s) saved to shopify!' % url)
            image.delete()
    #db.run_in_transaction(txn)
    
    txn()
    return ''
