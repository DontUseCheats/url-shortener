# url-shortener
Client-server architecture where Local Flask API shortens URLs, stores them in a database, and redirects visitors. Deployed on AWS (EC2 or Elastic Beanstalk), containerize it with Docker, and set up a GitHub Actions pipeline that automatically tests and deploys on every push.


# Goals
Main goal is about learning while building. Git commits will show tons of mistakes but the documentation will show my learning process. I'll also be adding notetaking, challenges, solutions and questions as I go along in the README

### Concepts to learn

Flask REST API  
DOCKER  
GitHub Actions CI/CD  
AWS deployment  
MySQL or DynamoDB (NoSQL) for storage

### Current understanding

Phase 1 - Local Flask API
	API code infrastructure that waits and listens for user inputted requests (URLs) and sends back responses. Essentially an endpoint that accepts and returns data. I’m assuming this is essentially where the URL is inputted and then shortened and redirected back to the user.

Phase 2 - Add MySQL to store URLs persistently
	Where shortened URLs are stored, essentially in a database. Without having a MySQL home to store the shortened URLs every instance of the code would reset its memory. MySQL gives it a permanent home.

Phase 3 - Containerize with Docker
	Packages your application, its dependencies, and its environments into one container where it would then be deployable and runs identically everywhere else. Consistency across environments.

Phase 4 - Deploy to AWS
	Deploy to AWS with EC2 allowing accessibility to users on the internet.

Phase 5 - Set up CI/CD with GitHub Actions
	Set up a Continuous Integration and Continuous Delivery where every push code update would automatically run tests. If tests pass, automatically deploy.

## Notes

Two different endpoints. One where URL shortening is created and is sent back to user. Two is when someone uses that short URL where they are then redirected to the original website.

    git checkout -b (name-of-branch)
    git branch

This is to create a new branch in the repo and git branch is what allows us to see which branch we're currently in.

    git push -u origin (name-of-branch)

When creating a new local branch for the first time we have to tell and push the branch to create it on GitHub too.

### secrets string
To create true randomness when shortening URLs we import secrets as its designed for security and cryptography while random is meant to be used for modelling and simulaton.

## flask
Initialized flask then we have to create two routes.  
One route for POST which is going to receive a long URL and then returns a short code  
Second route for GET where it looks up the code and redirects to the long URL

The first route I'm assuming would be the route where it receives the user inputted URL which is the POST and then that route would then return the shortened URL back. The second URL would be the redirecting part when the user actually clicks the new shortened URL where if the route detects the short URL route then it redirects to the original long url website which would be the GET

## Challenges/Process

### Phase 1 - Create local flask code
I first created a variable (alphabet) that contained random string values and numbers. Then created a function that when called returns a variable (short_url) with values containing 6 values of alphabet. Then created a while loop that checks if the newly short url already exists and if it does then reassign short url with the function call again. If it does not exist already then the code continues to where the dict is assigned the short url along with its long url partner. Refactored shorten code into one function which calls on create_short_url function.

### Obstacle 1 (POST request)
I had a challenging time understanding the POST request I was suppose to make.

    @app.route('/shorten', methods = ['POST'])
    def returns_short_url():
        long_url = request.get_json()
        long_url = long_url.get('url')
        new_short_url = shorten_url(long_url)
        return new_short_url

long_url.get('url') where 'url' is the chosen key name as written out in the Postman contract  
{"url": "https://example.com"}

 I created long_url then assigned it requests.get_json() which in theory would return {"url": "example.com"} What I didn't understand was how requests.get_json() was returning that example when all I did was initialize a new variable and assigned it to requests.get. I knew that requests.get_json() returns what the user inputted. But I didn't understand why they would input a dict instead of just the raw url link. What I found out was that when sending data over HTTP you can't just send a raw string. JSON is the standard format APIs use to structure data in requests and responses. It's the default industry standard and every real API works this way.

### GET request

Breaking the process down into chunks of what I need to do. The GET request has to first receive the short code from the URL path. In the GET route anything after / will cut and save it as the value in its parameters. As such

    @app.get('/<short_url>')
    def get_url(short_url):
        if short_url in dict_url:
            long_url = dict_url[short_url]
            return redirect(long_url)
        else:
            abort(404)

First line is the GET request and saves whatever is after / as the value to be stored in short_url. Then we def the get_url function and save the GET parameter value inside the function get_url parameters. Then if that short_url value which is the key finds and matches with itself in dict_url we initialize long_url as a new variable to hold the value of its key partner and then return its redirect route to the newly saved long_url. Else if it does not find a match then else we abort with error 404. 404 Not Found is the industry standard HTTP status code meaning the requested resource does not exist. Meaning short_url was not found in dict_url.

### Postman

Tested both routes using Postman with Flask running locally on 
http://127.0.0.1:5000. POST request to /shorten with a JSON body 
returns a short code with 200 OK. GET request to /<short_code> 
returns a 302 redirect to the original URL. 404 is returned if the 
short code doesn't exist in dict_url. Important: dict_url resets on 
every server restart since it lives in memory — this is why Phase 2 
adds MySQL for persistent storage.

### Phase 2 - Adding and refactoring for MySQL
### Obstacle 2 (Refactor function to MySQL)
My function def shorten_url(inputted_long_url) had to be refactored into MySQL comptability to connect with my code. Installed MySQL and library mysql.connector. I learned that when creating a connection to MySQL its better to create a function that initializes the connection rather than wrapping the whole code under one instance. Reason being is that connectivity issues or disconnection can cut the MySQL connection midway so its better to have individual instances to call the connector when needed. 

    # Function to connect MySQL to python
    def get_connection():
        connection = mysql.connector.connect(
            host = 'localhost',
            user = 'root',
            password = '',
            database = 'url_shortener'
        )
        return connection

---

    # Refactored function to MySQL connection with Python
    1 def shorten_url(inputted_long_url):
    2     new_short_url = create_short_url()
    3     connection = get_connection()
    4     cursor = connection.cursor()
    5     cursor.execute("SELECT short_url FROM urls where short_url = %s", (new_short_url,))
    6     fetched_url_row = cursor.fetchone()
    7     while fetched_url_row != None:
    8         new_short_url = create_short_url()
    9         cursor.execute("SELECT short_url FROM urls where short_url = %s", (new_short_url,))
    10        fetched_url_row = cursor.fetchone()
    11    cursor.execute("INSERT INTO urls (short_url, long_url) VALUES (%s, %s)", (new_short_url, inputted_long_url))
    12    connection.commit()
    13    cursor.close()
    14    connection.close()
    15    return new_short_url

Line 3: creates and assigns connection between MySQL and Python.  
Line 4: creates cursor object to execute commands and retrieve data through it  
Line 5: create MySQL command ("SELECT {column} FROM {table name} where {column} = {placeholder value}", (new_short_url,)) Has to be a tuple even with one value so trailing comma is required
Line 6: retrieves entire row from table, Returns None if no exact match between new_short_url and retrieved row  
Line 7-10: while loop check - if retrieved row doesn't equal the value of None then a duplicate was found so new url is created  
Line 11: execute command to insert new data  
Line 12-15: commit first, close open connections then return value

### Takeaways
MySQL commands written in python has to be between " " in order for python to know. %s serve as placeholder values to relate to whats being changed. Reason being is security standard to prevent SQL injection. With whats being changed after MySQL command "" needs to be a tuple example Line 9.

### GET route refactor to MySQL
    1 @app.get('/<short_url>')
    2 def get_url(short_url):
    3     connection = get_connection()
    4     cursor = connection.cursor()
    5     cursor.execute("SELECT long_url FROM urls WHERE short_url = %s", (short_url,))
    6     fetched_long_url = cursor.fetchone()
    7     if fetched_long_url == None:
    8         abort(404)
    9     fetched_long_url = fetched_long_url[0]
    10    cursor.close()
    11    connection.close()
    12    return redirect(fetched_long_url)

Line 3-4: Opening connecctions  
Line 5: Selecting long_url from table where short_url matches short_url in the database  
Line 6: Assign retrieved long url to variable fetched_long_url  
Line 7: If no match was found then rise error 404  
Line 9: fetchone retrieves a tuple so reassign fetched_long_url to first argument in tuple  
Line 10-11: close connections, no commit since no changes in database  
Line 12: return a redirect to the retrieved long url

### Phase 3 - Docker
Docker packages our whole application (code), dependencies (libraries) and its environments (Python, Ubuntu, OS) all into one package.  

Dockerfile -> Text file with instructions that tells Docker how to build your container.  
 1 -> Start with base image (Python on Ubuntu)  
 2 -> Set a working directory inside the container  
 3 -> Copy dependencies in  
 4 -> Install my dependencies 
 5 -> Copy code and install code   
 5 -> Run my app

docker-compose -> Tool that lets you run multiple containers together. For this project we'll have Flask app in one container and MySQL in another, connected together.  
 1 -> I have Flask container  
 2 -> I have MySQL container  
 3 -> Connect them together

Reason being is that if Flask and MySQL were under one container then multiple user created instances would create multiple MySQL databases. Two containers allow users to create multiple Flask instances while the other container (MySQL) is only run once with a persistent database across all Flask instances.

Dockerfile serves as the template for just our Flask container. The official Python image is just a starting point and it doesn't have our code, dependencies or the main.py file. Dockerfile serves as a base image and then we add everything specific about our app on top of it. 

MySQL is different. The official MySQL image is already a complete ready to run database server. We just need to configure it with environment variables (password, database name) in docker-compose.

Essentially:  
 - Flask -> needs a Dockerfile because we're building on top of the Python base image with our own code  
 - MySQL -> No Dockerfile needed, the official immage is complete as is and just needs configuration in docker-compose
 
 ### Takeaways
### What is Docker?
Docker is software that packages your application, its dependencies, 
and its environment into a container that runs identically anywhere 
Docker is installed — your laptop, a teammate's machine, or an AWS server.

### Files Created

**Dockerfile** — a blueprint that tells Docker how to build the Flask 
container. It specifies the Python version, creates a working directory 
(/app), copies and installs dependencies from requirements.txt first 
(for layer caching — so dependencies don't reinstall on every code change), 
then copies main.py and runs it with CMD.

**docker-compose.yml** — the instruction manual that defines and 
orchestrates both containers (called services):
- `mysql-db` — pulls the official MySQL 8.0 image from Docker Hub and 
configures it with environment variables (database name and root password)
- `web` — builds the Flask container from our Dockerfile, maps port 5000, 
syncs local code via volumes, and depends_on mysql-db so MySQL starts first

We keep Flask and MySQL in separate containers so only one MySQL instance 
runs regardless of how many Flask containers are running — keeping the 
database persistent and consistent across instances.

**init.sql** — the MySQL container starts fresh with only the database 
created via environment variable. init.sql runs automatically on first 
startup via /docker-entrypoint-initdb.d/ and creates the urls table with 
its three columns: id, short_url, and long_url.

**requirements.txt** — lists all Python dependencies (flask, 
mysql-connector-python) so Docker can install them automatically 
during the build.

### Key Changes in main.py
Two changes were needed for Docker compatibility:
1. Changed host='localhost' to host='mysql-db' in get_connection() — 
inside Docker, localhost refers to the container itself. Flask finds 
MySQL using the service name 'mysql-db' since they're in separate containers.
2. Changed app.run(debug=True) to app.run(host='0.0.0.0', debug=True) — 
by default Flask only listens inside its own container. 0.0.0.0 tells 
Flask to listen on all network interfaces so your machine can reach it.

### Docker Commands
- `sudo docker compose up --build -d` — builds and starts all containers 
in detached mode (runs in background)
- `sudo docker compose stop` — stops containers but keeps data
- `sudo docker compose down` — stops and removes containers (data lost 
without named volume)
- `sudo docker ps` — lists all running containers

### Data Persistence Notes
Current setup: data persists across stop/start but not across down/up.

Saved for later:
- Add MySQL named volume so data survives docker compose down
- Use AWS RDS in Phase 4 as the production database 
(single source of truth for all users)