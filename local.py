#!python3
#
# For testing only
#
if __name__ == '__main__':

    from mensa import wsgi
    from wsgiref.simple_server import make_server
    httpd = make_server('localhost', 80, wsgi.application)
    print("http://localhost:80/")
    httpd.serve_forever()
