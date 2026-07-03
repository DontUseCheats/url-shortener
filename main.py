from flask import Flask, request, abort, redirect
import secrets
import string


# Flask app initialization
app = Flask(__name__)


# Declare empty dict
dict_url = {}

# Generate random letters and numbers
alphabet = string.ascii_letters + string.digits


# Assign short_url with 6 random letters and numbers
def create_short_url():
    new_short_url = ''.join(secrets.choice(alphabet) for i in range(6))
    return new_short_url

# Shorten long url to short url with while check
def shorten_url(inputted_long_url):
    new_short_url = create_short_url()
    while new_short_url in dict_url:
        new_short_url = create_short_url()
    dict_url[new_short_url] = inputted_long_url
    return new_short_url

# POST route (later on needs postman for request.get_json)
@app.route('/shorten', methods = ['POST'])
def returns_short_url():
    long_url = request.get_json()
    long_url = long_url.get('url')
    new_short_url = shorten_url(long_url)
    return new_short_url

# GET route
@app.get('/<short_url>')
def get_url(short_url):
    if short_url in dict_url:
        long_url = dict_url[short_url]
        return redirect(long_url)
    else:
        abort(404)

# flask run
if __name__ == "__main__":
    app.run(debug=True)