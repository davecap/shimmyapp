"""
Initialize Flask app and Shopify extension
"""

from flask import Flask
from flaskext.shopify import Shopify

app = Flask('application')
app.config.from_object('application.settings')

try:
    app.config.from_object('application.shopify')
except:
    raise Exception('Set your Shopify API settings in applications.shopify')

shopify = Shopify(app)

import views
