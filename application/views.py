"""
Flask Module Docs:  http://flask.pocoo.org/docs/api/#flask.Module

This file is used for both the routing and logic of your
application.
"""

from flask import url_for, render_template, request, redirect, flash, session, make_response
from werkzeug.exceptions import BadRequest
import logging
import urllib
import urlparse

from application import app, shopify
from flaskext.shopify import shopify_login_required

from application.models import Image, Shop

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
        dbshop = Shop.all().filter("url =", shopify_session.url)
        if len(dbshop) == 0:
            shop = request.shopify_session.Shop.current().to_dict()
            dbshop = Shop(  name = shop['name'],
                            domain = shopify_session.url,
                            password = shopify_session.password
                        )
            dbshop.put()
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

@shopify_login_required
@app.route('/product/<int:product_id>')
def product(product_id):
    shop = request.shopify_session.Shop.current().to_dict()
    product = request.shopify_session.Product.find(product_id).to_dict()
    images = Image.all().filter("shop_domain =", shop['domain']).filter("product_id =", product_id)
    upload_images = [ i.url() for i in images ]
    return render_template('product.html', shop=shop, product=product, upload_images=upload_images)

@shopify_login_required
@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        f = request.files['file']
        product_id = int(request.form['product_id'])        
        # create a new Image object
        image = Image(  shop_domain = request.shopify_session.url,
                        product_id = product_id,
                        product_handle = request.form['product_handle'],
                        image = f.stream.read(),
                        mimetype = f.content_type,
                        filename = f.filename
                    )
        image.put()
                
        # update shopify product
        product = request.shopify_session.Product.find(product_id)
        product.images.append({ "src": urlparse.urljoin('http://'+app.config['SERVER_NAME'], image.url()) })
        if not product.save():
            logging.error('Error saving product to Shopify!')
        
        response = redirect(request.form['next'])
        response.data = ''
        return response
    else:
        return render_template('500.html'), 500

@app.route('/shop/<string:shop_domain>/images/<string:product_handle>_<int:key_id>.jpg')
def image(shop_domain, product_handle, key_id):
    product_handle = str(urllib.unquote(product_handle))
    shop_domain = str(urllib.unquote(shop_domain))
        
    i = Image.get_by_id(key_id)
    
    if i.shop_domain == shop_domain and i.product_handle == product_handle:
        # show the blob
        response = make_response(i.image)
        response.headers['Content-Type'] = i.mimetype
        return response
    else:
        render_template('404.html'), 404

def allowed_file(filename): 
    """Check to make sure the file is an image.""" 
    allowed_extensions = ['jpg', 'jpeg', 'gif', 'png'] 
    return filename.rsplit('.', 1)[1].lower() in allowed_extensions