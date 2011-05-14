import os
import sys
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from google.appengine.dist import use_library
use_library('django', '1.2')
package_dir = "libs"
sys.path.insert(0, package_dir)
for filename in os.listdir(package_dir):
    if filename.endswith((".zip", ".egg")):
        sys.path.insert(0, "%s/%s" % (package_dir, filename))

from application.models import Image

class ImageHandler(webapp.RequestHandler):
    def head(self, key_id, filename):
        self.get(key_id, filename)

    def get(self, key_id, filename):
        logging.error("GET %s   %s" % (key_id, filename))
        i = Image.get_by_id(int(key_id))
        if not i:
            self.error(404)
        self.response.headers['Content-Type'] = i.mimetype
        self.response.out.write(i.image)

def main():
    application = webapp.WSGIApplication([
        ('/i/(.*)/(.*)', ImageHandler),
    ], debug=True)
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

