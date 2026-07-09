# README
> **Note:** This README was first written through my own raw input of 
> thought process, documentation and questions I had asked in Claude. 
> Look at earlier commits to read the raw process. Only then was it 
> refactored into Claude for the sole purpose of a cleaner and easier 
> understanding process.

# url-shortener
A backend service that shortens URLs, stores them in a database, and 
redirects visitors. Built with Flask, MySQL, Docker, and deployed to AWS 
with a GitHub Actions CI/CD pipeline.

This project is primarily a learning exercise. Every phase was built 
bit by bit with the goal of understanding each piece before moving to 
the next. README shows the documentation and learning/thought process.

---

# Goals
- Build a real backend service from scratch
- Learn Flask REST API design
- Learn MySQL database integration
- Learn Docker containerization
- Learn AWS deployment
- Learn CI/CD with GitHub Actions

---

## My Understanding Before Starting (Pre-Work)

### Phase 1 - Local Flask API
API code infrastructure that waits and listens for user inputted requests 
(URLs) and sends back responses. Essentially an endpoint that accepts and 
returns data. I'm assuming this is essentially where the URL is inputted 
and then shortened and redirected back to the user.

### Phase 2 - Add MySQL to store URLs persistently
Where shortened URLs are stored, essentially in a database. Without having 
a MySQL home to store the shortened URLs every instance of the code would 
reset its memory. MySQL gives it a permanent home.

### Phase 3 - Containerize with Docker
Packages your application, its dependencies, and its environments into one 
container where it would then be deployable and runs identically everywhere 
else. Consistency across environments.

### Phase 4 - Deploy to AWS
Deploy to AWS with EC2 allowing accessibility to users on the internet.

### Phase 5 - Set up CI/CD with GitHub Actions
Set up a Continuous Integration and Continuous Delivery where every push 
code update would automatically run tests. If tests pass, automatically 
deploy.

---

## What Each Phase Actually Does (Post-Work)

### Phase 1 - Local Flask API
Two separate HTTP endpoints. POST /shorten receives a long URL and returns 
a generated short code. GET /<short_code> looks up that code and redirects 
the user to the original URL. These are completely separate interactions — 
one creates the mapping, one uses it.

### Phase 2 - MySQL Integration
Replaces in-memory dict storage with a persistent MySQL database. Data now 
survives server restarts. Introduced SQL, the mysql-connector-python library, 
cursors, and the get_connection() pattern.

### Phase 3 - Docker
Two containers — one for Flask, one for MySQL — orchestrated by 
docker-compose. The Dockerfile builds the Flask image. init.sql initializes 
the database table on first startup. docker-compose connects everything.

### Phase 4 - AWS Deployment
The Docker containers are deployed to an AWS EC2 instance giving the app 
a real public URL accessible from anywhere on the internet.

### Phase 5 - CI/CD with GitHub Actions
A GitHub Actions workflow automatically runs on every push — tests the code 
and if tests pass, deploys the latest version to AWS automatically.

---

## Git Workflow
One branch per phase. Main always has stable working code. Never work 
directly on main.

    git checkout -b phase-name                     # create and switch to branch
    git branch                                     # see all branches, * = current
    git push --set-upstream origin phase-name      # first push of new branch
    git push                                       # subsequent pushes
    git checkout main && git merge phase-name      # merge completed phase

Commit messages use imperative style: "Add route" not "Added route"

---

## Phase 1 - Local Flask API

### What I was building
A Flask app with two endpoints:
- POST /shorten — user sends a long URL, app returns a short code
- GET /<short_code> — user visits the short code, app redirects to original URL

These are two completely separate interactions. Shortening creates the 
mapping. Redirecting uses it later. The person shortening and the person 
clicking don't have to be the same — someone shares a short link with 
thousands of people and each click is its own redirect request hitting 
the server.

### Short code generation
Used secrets.choice instead of random because secrets is designed for 
cryptographic randomness — it's genuinely unpredictable. random is for 
simulations and games. If short codes were predictable someone could 
guess them. 6 characters from 62 possible (a-z, A-Z, 0-9) gives 56 
billion combinations — more than enough.

    alphabet = string.ascii_letters + string.digits
    new_short_url = ''.join(secrets.choice(alphabet) for i in range(6))

### Two functions, one job each
Kept create_short_url() and shorten_url() separate — separation of concerns. 
Each function does one thing. create_short_url() just generates a code. 
shorten_url() handles the collision check and storage. The route just 
calls shorten_url() and returns the result.

### Collision check — understanding the while loop direction
Before saving a short code, check if it already exists. The first instinct 
was to write:

    while new_short_url not in dict_url:
        dict_url[new_short_url] = inputted_long_url

This is backwards. "while the code is NOT in 
the dict, keep adding it." That adds the same code over and over on the 
happy path (industry standard terminology) and does nothing when there's a collision.

The correct logic: the while loop's only job is regenerating. The dict 
assignment happens after the loop exits — at that point you're guaranteed 
a free code.

    new_short_url = create_short_url()
    while new_short_url in dict_url:    # if taken, keep regenerating
        new_short_url = create_short_url()
    dict_url[new_short_url] = inputted_long_url  # guaranteed free

Used while not for because you don't know how many attempts it'll take. 
A for loop runs a fixed number of times. while runs until a condition is met.

### Flask initialization — what __name__ means
    app = Flask(__name__)

__name__ is a built-in Python variable. When you run a file directly, 
Python sets __name__ to "__main__". When a file is imported by something 
else, __name__ is set to the module name instead. Flask uses this to know 
where to look for files and resources. The if __name__ == "__main__" 
check at the bottom means "only start the server if this file is run 
directly, not if it's imported." Important for Docker and other tools 
that import your app without wanting to start the server.

### Obstacle 1 — Understanding POST and request.get_json()
This took a while to understand as I didn't have prior knowledge of Postman. I created long_url = request.get_json() 
and while looking at examples I couldn't understand how Flask knew to return {"url": "https://example.com"} 
when I never defined that anywhere.

The answer: it doesn't know. request represents whatever the user sends. 
get_json() reads the request body and converts it from JSON to a Python dict. 
The format {"url": "..."} is the API contract I decided on in Postman, users must 
send data in that format. In Postman I play the role of the user and send 
exactly that.

The follow-up confusion: why send a dict at all? Why not just the raw URL?

The answer: industry standard. When sending data over HTTP you can't just 
send a raw string. JSON is what every API, frontend, and tool expects. It's 
also easier to extend, if you later want to add a custom alias alongside 
the URL, JSON handles that with no restructuring.

### Routes

POST /shorten:
    @app.route('/shorten', methods=['POST'])
    def returns_short_url():
        long_url = request.get_json()       # read JSON body from request
        long_url = long_url.get('url')      # extract just the URL string
        new_short_url = shorten_url(long_url)
        return new_short_url

GET /<short_code>:
    @app.get('/<short_url>')
    def get_url(short_url):
        if short_url in dict_url:
            long_url = dict_url[short_url]
            return redirect(long_url)       # 302 redirect
        else:
            abort(404)

Flask captures whatever comes after / and passes it into the function 
as short_url automatically — that's Flask variable rules. The variable 
name inside <> and the function parameter must match, that's how Flask 
delivers the captured value.

302 means "found, go here instead." Browser follows it automatically — 
that's what makes short URLs feel seamless. 404 is the industry standard 
HTTP status code meaning the requested resource does not exist — in this 
case the short code wasn't found.

### Obstacle 2 — url_for vs redirect()
First attempt at the GET route used url_for():

    return redirect(url_for(long_url))

url_for() generates URLs to other routes inside your own Flask app — for 
example linking to your /shorten endpoint. It's not for external URLs. 
Since we're redirecting to an external URL like https://www.google.com, 
redirect() takes the URL string directly:

    return redirect(long_url)

The distinction: url_for() is internal navigation. redirect() with a 
direct URL is external navigation.

### Testing with Postman
A browser can only easily send GET requests. Postman lets you craft any 
HTTP request — method, body, headers — simulating what a real frontend 
would send.

Tested locally on http://127.0.0.1:5000  
(127.0.0.1 always means "this machine", port 5000 is Flask's default.
Understanding ports as unique identifiers, Flask listens at unique identifier number 5000, 
MySQL listens at 3306, web traffic uses 80 or 443)

- POST to /shorten with {"url": "https://www.google.com"} → short code, 200 OK
- GET to /<short_code> → Google's HTML, 302 redirect
- 404 if short code doesn't exist

First GET test returned 404 — thought something was wrong. Realized the 
server had restarted and dict_url wiped clean. This is exactly why Phase 
2 exists.

---

## Phase 2 - MySQL Integration

### Why MySQL
dict_url lives in memory. Every server restart wipes it. MySQL stores 
data permanently on disk where it survives restarts, crashes, and eventually 
multiple servers running the same app simultaneously.

### What is MySQL
MySQL is a relational database management system. SQL is the language — 
SELECT, INSERT, UPDATE, DELETE. MySQL is one of many systems that speaks 
SQL — PostgreSQL, SQLite, and others use the same core language with 
minor differences. What I learn here transfers directly.

The hierarchy:
    MySQL Server
    └── url_shortener (database)   ← container for tables
        └── urls (table)           ← like a spreadsheet
            ├── id                 ← unique auto-incrementing number
            ├── short_url          ← the generated short code
            └── long_url           ← the original URL

### Setup in terminal
    sudo mysql -u root -p
    CREATE DATABASE url_shortener;
    USE url_shortener;
    CREATE TABLE IF NOT EXISTS urls (
        id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
        short_url VARCHAR(10),
        long_url VARCHAR(2048)
    );

### get_connection() pattern
Instead of one global connection at the top of the file, created a 
function that makes a fresh connection when called. A global connection 
risks timing out or dropping mid-operation. Individual connections per 
function call is safer and is the standard pattern for small Flask apps.

    def get_connection():
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='password',
            database='url_shortener'
        )
        return connection

### How Python talks to MySQL
Three pieces work together:
- connection — the phone call to MySQL
- cursor — the voice doing the talking (executes SQL)
- execute() — sends the actual SQL command

Always use %s placeholders, never put values directly in the SQL string. 
This prevents SQL injection — a security attack where malicious input 
manipulates your query. The connector handles sanitization when you use %s.

### Refactored shorten_url()
    def shorten_url(inputted_long_url):
        new_short_url = create_short_url()
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT short_url FROM urls WHERE short_url = %s",
                      (new_short_url,))          # tuple required even for one value
        fetched_url_row = cursor.fetchone()      # None if no match found
        while fetched_url_row != None:           # collision — regenerate
            new_short_url = create_short_url()
            cursor.execute("SELECT short_url FROM urls WHERE short_url = %s",
                          (new_short_url,))
            fetched_url_row = cursor.fetchone()
        cursor.execute("INSERT INTO urls (short_url, long_url) VALUES (%s, %s)",
                      (new_short_url, inputted_long_url))
        connection.commit()    # like hitting save — makes changes permanent
        cursor.close()
        connection.close()
        return new_short_url

### Understanding commit
commit() was confusing at first — why do you need to explicitly save? 
MySQL wraps changes in transactions. You can make multiple changes and 
either commit them all at once or roll them back if something goes wrong. 
commit() is the "confirm and save" step. Without it the INSERT runs but 
nothing actually gets saved permanently. Only needed for INSERT, UPDATE, 
DELETE — not for SELECT since you're not changing anything.

### Understanding fetchone() returning a tuple
cursor.fetchone() returns a row as a tuple, not a plain value. So even 
though you only selected one column, you get back ('aB3xZ',) not 'aB3xZ'. 
To get just the string, extract the first item:

    fetched_long_url = fetched_long_url[0]

This caught me off guard — the data is there but wrapped in a tuple. 
Always remember fetchone() returns a tuple or None.

### Refactored GET route
    def get_url(short_url):
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT long_url FROM urls WHERE short_url = %s",
                      (short_url,))
        fetched_long_url = cursor.fetchone()
        if fetched_long_url == None:
            abort(404)
        fetched_long_url = fetched_long_url[0]  # extract from tuple
        cursor.close()
        connection.close()                       # no commit — read only
        return redirect(fetched_long_url)

### Obstacle 3 — Access Denied
Got 500 error: "Access denied for user 'root'@'localhost'". Ubuntu's MySQL 
installs root with auth_socket authentication by default — sudo mysql works 
but the Python connector can't connect that way. Fixed by switching root to 
password authentication:

    ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'password';
    FLUSH PRIVILEGES;

This also meant updating get_connection() to use password='password'.

---

## Phase 3 - Docker

### What is Docker and why it exists
Without Docker: "it works on my machine" is a real problem. Different 
Python versions, different OS, different dependencies installed — code 
that works locally can fail on a server or teammate's machine.

Docker solves this by packaging your app, its dependencies, and its 
environment into a container that runs identically anywhere Docker is 
installed. Not a virtual machine — containers share the host OS kernel 
but have their own isolated environment on top. Much lighter than a VM, 
starts in seconds.

### Image vs Container
A Dockerfile is a text file with instructions that tells Docker how to 
build your app. When you run docker build, Docker reads those instructions 
and produces an Image — a complete, packaged, ready-to-run version of your 
app frozen in time. Good to think of the image as the finished, installable package.

A Container is what you get when you actually run that image. It's the 
live, running instance of your app. You can run multiple containers from 
the same image — each one is independent.

So the process is:
1. You write the Dockerfile (the instructions)
2. Docker builds it into an Image (the package)
3. You run the Image to create a Container (the running app)

### Why two containers
Keeping Flask and MySQL in separate containers means only one MySQL 
instance runs regardless of how many Flask containers are running. This 
was a key insight and learning step. If they were in the same container, scaling Flask 
would create multiple databases. Separated, you can run as many Flask 
instances as you need while the one MySQL container holds all the data.

### Docker Hub
Public registry of pre-built images. FROM python:3.12 and 
image: mysql:8.0 are pulled from Docker Hub automatically. You don't 
build Python or MySQL from scratch — you start from official images and 
add what's specific to your app on top.

Flask needs a Dockerfile because the official Python image is just a 
starting point — it doesn't have our code or dependencies. MySQL doesn't 
need a Dockerfile because the official MySQL image is already a complete 
ready-to-run database server. Just configure it with environment variables.

### Dockerfile (Flask container blueprint)
    FROM python:3.12          # start from official Python image
    WORKDIR /app              # create and use /app as working directory
    COPY requirements.txt .   # copy dependencies list first
    RUN pip install --no-cache-dir -r requirements.txt  # install them
    COPY main.py .            # copy code after
    CMD ["python", "main.py"] # run this when container starts

Why copy requirements.txt and main.py separately? Layer caching. Docker 
caches each build step. If you copy everything at once, any change to 
main.py forces Docker to reinstall all dependencies even if they didn't 
change. Separated, dependencies only reinstall when requirements.txt 
changes. Keeps rebuilds fast.

### requirements.txt
    flask
    mysql-connector-python

Standard Python convention — lists all external packages so any system 
(Docker, a teammate, a CI pipeline) can install them without knowing 
what the code uses. secrets and string are not listed because they're 
Python standard library — built in, no installation needed.

### docker-compose.yml
    services:
      mysql-db:
        image: mysql:8.0
        environment:
          - MYSQL_DATABASE=url_shortener  # creates DB on first startup
          - MYSQL_ROOT_PASSWORD=password
        ports:
          - "3306:3306"                   # host:container
        volumes:
          - ./init.sql:/docker-entrypoint-initdb.d/init.sql

      web:
        build: .              # build from Dockerfile in current directory
        container_name: flask_code
        ports:
          - "5000:5000"
        volumes:
          - .:/app            # sync local folder to /app in container
        depends_on:
          - mysql-db          # don't start Flask until MySQL is ready

Service names (mysql-db, web) are not just labels — they become hostnames 
that containers use to find each other on Docker's internal network. This was important to learn and understand as later on in Obstacle 4 main.py will be updated. Specifically 'localhost' and app.run(debug=True).

### init.sql
The MySQL container creates the database automatically via environment 
variable but not the tables. Any .sql file placed in 
/docker-entrypoint-initdb.d/ runs automatically on first startup.

    CREATE TABLE IF NOT EXISTS urls (
        id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
        short_url VARCHAR(10) NOT NULL UNIQUE,
        long_url VARCHAR(2048) NOT NULL
    );

### Volumes explained
Two different volume uses in this project:

.:/app (Flask) — mounts entire local project into /app in the container. 
Changes made locally appear instantly without rebuilding. . is the 
current directory (entire folder), /app is the WORKDIR destination.

./init.sql:/docker-entrypoint-initdb.d/init.sql (MySQL) — mounts just 
one specific file. The difference:
- . = entire current directory
- ./init.sql = just this one file in the current directory

### Obstacle 4 — Two changes needed in main.py

Change 1: host='localhost' → host='mysql-db'
Inside Docker, localhost refers to the container itself — not the MySQL 
container next to it. Each container is its own isolated environment. 
Docker's networking maps service names to container IPs automatically, 
so 'mysql-db' routes to the MySQL container. Same concept as changing 
a hardcoded path to a variable — you're telling things where to look 
across container boundaries.

Change 2: app.run(debug=True) → app.run(host='0.0.0.0', debug=True)
Flask defaults to listening on 127.0.0.1 — only inside its own container. 
Nothing outside can reach it, including your machine even though port 
5000 is mapped. 0.0.0.0 means "listen on all network interfaces" — 
including the one Docker exposes through the port mapping. Without this 
change Postman gets "socket hang up" even with the port correctly mapped.

### Obstacle 5 — Port conflict on first run
First docker compose run failed: "address already in use" on port 3306. 
My local MySQL service was already running and claimed that port. Docker's 
MySQL container couldn't bind to it. Fixed by stopping local MySQL:

    sudo service mysql stop

Local MySQL is no longer needed — Docker runs its own completely separate 
MySQL instance. The two don't share data or configuration.

### Obstacle 6 — Old docker-compose version bug
The version installed via apt (docker-compose with hyphen) had a 
ContainerConfig bug that prevented rebuilding containers. Fixed by 
installing the newer Docker Compose plugin (docker compose with space):

    sudo apt install docker-compose-plugin
    sudo docker compose up --build -d

### Docker Commands
    sudo docker compose up --build -d   # build and start in background
    sudo docker compose stop            # pause containers, data safe
    sudo docker compose down            # remove containers
    sudo docker ps                      # list running containers
    sudo docker exec -it <name> mysql -u root -p  # access MySQL inside container

### Understanding detached mode (-d)
Without -d, docker compose up takes over your terminal and streams all 
container logs. You can't run other commands. With -d (detached), 
containers run in the background and your terminal is free. Use 
sudo docker ps to check status and sudo docker logs <name> to see logs.

### Data Persistence — stop vs down
This distinction matters more than it seems:

- stop → containers paused, data safe (like sleep mode)
- down → containers removed, data gone

Named volume would fix the down problem — stores MySQL data in a Docker 
managed volume that exists independently of the container. Even after 
docker compose down destroys the container, the volume survives. Next 
docker compose up mounts the same volume with all existing data.

### Named volume vs AWS RDS — two different problems
These solve different things entirely:

Named volume — "my data survives on my machine across container restarts"
AWS RDS — "everyone shares the same data regardless of where they're running"

Named volume is a local persistence solution. RDS is a cloud database 
that every environment (your laptop, AWS server, teammate's machine) 
connects to. In production you'd want both concepts — RDS for the shared 
data and proper container management for restarts.

---

## Saved for Later
- Click tracking — log every redirect with timestamp, IP, user agent
- MySQL named volume — persist data across docker compose down locally
- AWS RDS — managed cloud database as single source of truth in production