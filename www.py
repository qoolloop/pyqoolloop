

def check_url(url):
    return url.find('"') < 0  #TODO: better validation. It might be best to make sure the path points to an endpoint
    # http://homakov.blogspot.jp/2014/01/evolution-of-open-redirect-vulnerability.html
    # http://validators.readthedocs.io/en/latest/#module-validators.url
    # https://stackoverflow.com/questions/35149861/equivalent-urllib-parse-quote-in-python-2-7
    # http://flask.pocoo.org/snippets/62/
