from flask import Flask, request, abort, redirect
import secrets
import string
import mysql.connector


# Flask app initialization
app = Flask(__name__)

# Generate random letters and numbers
alphabet = string.ascii_letters + string.digits


# Function to connect MySQL to python
def get_connection():
    connection = mysql.connector.connect(
        host = 'mysql-db',
        user = 'root',
        password = 'password',
        database = 'url_shortener'
    )
    return connection

# Assign short_url with 6 random letters and numbers
def create_short_url():
    new_short_url = ''.join(secrets.choice(alphabet) for i in range(6))
    return new_short_url

# Refactored function to MySQL connection with Python
def shorten_url(inputted_long_url):
    new_short_url = create_short_url()
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT short_url FROM urls where short_url = %s", (new_short_url,))
    fetched_url_row = cursor.fetchone()
    while fetched_url_row != None:
        new_short_url = create_short_url()
        cursor.execute("SELECT short_url FROM urls where short_url = %s", (new_short_url,))
        fetched_url_row = cursor.fetchone()
    cursor.execute("INSERT INTO urls (short_url, long_url) VALUES (%s, %s)", (new_short_url, inputted_long_url))
    connection.commit()
    cursor.close()
    connection.close()
    return new_short_url


# POST route (Postman contract testing for request.get_json)
@app.route('/shorten', methods = ['POST'])
def returns_short_url():
    long_url = request.get_json()
    long_url = long_url.get('url')
    new_short_url = shorten_url(long_url)
    return new_short_url

# GET route Refactored into MySQL
@app.get('/<short_url>')
def get_url(short_url):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT long_url FROM urls WHERE short_url = %s", (short_url,))
    fetched_long_url = cursor.fetchone()
    if fetched_long_url == None:
        abort(404)
    fetched_long_url = fetched_long_url[0]
    cursor.close()
    connection.close()
    return redirect(fetched_long_url)


# flask run
if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)