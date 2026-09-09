# NOTES

Phase-by-phase learning process, obstacles, and terms for the 
url-shortener project. See [README.md](./README.md) for the 
project overview.

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

This is backwards. "while the code is NOT in the dict, keep adding it." 
That adds the same code over and over on the happy path (industry standard 
terminology for the expected, error-free flow) and does nothing when there's 
a collision.

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
This took a while to understand as I didn't have prior knowledge of Postman. 
I created long_url = request.get_json() and while looking at examples I 
couldn't understand how Flask knew to return {"url": "https://example.com"} 
when I never defined that anywhere.

The answer: it doesn't know. request represents whatever the user sends. 
get_json() reads the request body and converts it from JSON to a Python dict. 
The format {"url": "..."} is the API contract I decided on in Postman — users 
must send data in that format. In Postman I play the role of the user and 
send exactly that.

The follow-up confusion: why send a dict at all? Why not just the raw URL?

The answer: industry standard. When sending data over HTTP you can't just 
send a raw string. JSON is what every API, frontend, and tool expects. It's 
also easier to extend — if you later want to add a custom alias alongside 
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
Ports are unique identifiers — Flask listens at 5000, MySQL at 3306, 
web traffic uses 80 or 443)

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
and produces an Image — the complete, packaged, ready-to-run version of 
the app frozen at that point in time.

A Container is what you get when you actually run that image. It's the 
live, running instance of the app. You can run multiple containers from 
the same image where each container is independent.

So the process is:
1. You write the Dockerfile (the instructions)
2. Docker builds it into an Image (the package)
3. You run the Image to create a Container (the running app)

### Why two containers
Keeping Flask and MySQL in separate containers means only one MySQL 
instance runs regardless of how many Flask containers are running. This 
was a key insight — if they were in the same container, scaling Flask 
would create multiple databases. Separated, you can run as many Flask 
instances as you need while the one MySQL container holds all the data.

Flask and MySQL run continuously on EC2 — not per user. Flask handles 
multiple users simultaneously through request handling. One Flask container 
can serve hundreds of requests at the same time. MySQL runs continuously 
and serves as the single database for everyone.

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
that containers use to find each other on Docker's internal network. This 
becomes important in Phase 4 when main.py needs to be updated to use 
'mysql-db' instead of 'localhost'.

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
so 'mysql-db' routes to the MySQL container.

Change 2: app.run(debug=True) → app.run(host='0.0.0.0', debug=True)
Flask defaults to listening on 127.0.0.1 — only inside its own container. 
Nothing outside can reach it, including your machine even though port 
5000 is mapped. 0.0.0.0 means "listen on all network interfaces" — 
including the one Docker exposes through the port mapping. Without this 
change Postman gets "socket hang up" even with the port correctly mapped.

### Obstacle 5 — Port conflict on first run
First docker compose run failed: "address already in use" on port 3306. 
Local MySQL service was already running and claimed that port. Docker's 
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
    sudo docker compose down -v         # remove containers AND volumes
    sudo docker ps                      # list running containers
    sudo docker logs <name> --follow    # watch container logs in real time
    sudo docker exec -it <name> mysql -u root -p  # access MySQL inside container

### Understanding detached mode (-d)
Without -d, docker compose up takes over your terminal and streams all 
container logs. You can't run other commands. With -d (detached), 
containers run in the background and your terminal is free. Use 
sudo docker ps to check status and sudo docker logs <name> to see logs.

### Data Persistence — stop vs down
- stop → containers paused, data safe (like sleep mode)
- down → containers removed, data gone
- down -v → containers AND volumes removed, complete clean slate

Named volume would fix the down problem — stores MySQL data in a Docker 
managed volume that exists independently of the container. Even after 
docker compose down destroys the container, the volume survives. Next 
docker compose up mounts the same volume with all existing data.

### Named volume vs AWS RDS — two different problems
Named volume — "my data survives on my machine across container restarts"
AWS RDS — "everyone shares the same data regardless of where they're running"

Named volume is a local persistence solution. RDS is a cloud database 
that every environment (your laptop, AWS server, teammate's machine) 
connects to. In production you'd want both concepts — RDS for the shared 
data and proper container management for restarts.

---

## Phase 4 - AWS Deployment

### What is AWS EC2 and why we need it
EC2 (Elastic Compute Cloud) is a virtual machine running in Amazon's data 
center. Your app right now only runs on your laptop — when you close it 
the app goes down and nobody can reach it. EC2 gives you a computer that:
- Is always on
- Has a public IP address anyone on the internet can reach
- Runs your Docker containers 24/7

### What is ECR and why we need it
ECR (Elastic Container Registry) is AWS's private Docker image registry. 
Your Docker image lives on your laptop. EC2 is a completely separate 
computer in Amazon's data center with no access to your machine. ECR is 
the middleman — you push your image there, EC2 pulls it from there.

Think of it like GitHub but for Docker images instead of code:
- GitHub stores your code, any machine can clone it
- ECR stores your Docker images, any server can pull it

MySQL doesn't need ECR because it uses the official public mysql:8.0 image 
from Docker Hub — EC2 pulls it directly. Only your custom Flask image 
needs ECR since it's private.

### Step by step — what we did and why

**Step 1 — Install AWS CLI on local machine**

    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install

The AWS CLI lets you interact with AWS services from your terminal. Same 
concept as how you interact with Docker and MySQL from the terminal — 
instead of clicking through the AWS console, you run commands. We did 
this in the terminal rather than clicking through the AWS console because 
in Phase 5 GitHub Actions needs to run these exact commands automatically — 
you can't click through a UI in an automated pipeline.

**Step 2 — Create IAM access key and configure CLI**

    aws configure

Never use the root account for day to day work — industry standard. Created 
an IAM user with specific permissions. Generated access keys (Access Key ID 
and Secret Access Key) which are the credentials that authenticate your 
terminal to your AWS account. Like logging in but for the CLI.

    aws sts get-caller-identity  # verify credentials are working

**Step 3 — Create ECR repository**

    aws ecr create-repository --repository-name url-shortener --region us-west-1

Creates an empty storage location in AWS — like creating an empty GitHub repo. 
Returns a repositoryUri that you'll use to tag and push your image.

    repositoryUri: 801498844513.dkr.ecr.us-west-1.amazonaws.com/url-shortener

**Step 4 — Authenticate Docker to ECR**

    aws ecr get-login-password --region us-west-1 | sudo docker login --username AWS --password-stdin 801498844513.dkr.ecr.us-west-1.amazonaws.com

AWS CLI and Docker are two separate systems. Docker has no idea about your 
AWS credentials. This command uses your AWS credentials to generate a 
temporary Docker login token (valid 12 hours) and passes it to Docker. 
After this Docker has permission to push/pull from your private ECR repository.

Must be re-run every session since the token expires after 12 hours.

**Step 5 — Build Docker image locally**

    sudo docker build -t url-shortener .

Reads the Dockerfile in the current directory (.) and builds a Docker image 
called url-shortener stored locally on your machine. The . tells Docker to 
look in the current directory — which is why you must cd into your project 
folder first.

**Step 6 — Tag image with ECR URI**

    sudo docker tag url-shortener:latest 801498844513.dkr.ecr.us-west-1.amazonaws.com/url-shortener:latest

The image built in Step 5 is just called url-shortener locally — Docker has 
no idea where it's supposed to go. Tagging renames it to include the full 
ECR address. Think of it like putting a shipping address on a package. The 
package is built, but without the address Docker doesn't know where to 
deliver it.

**Step 7 — Push image to ECR**

    sudo docker push 801498844513.dkr.ecr.us-west-1.amazonaws.com/url-shortener:latest

This is the actual step that sends the image from your machine to ECR. 
Each layer of the image gets uploaded separately. Once pushed EC2 can pull it.

**Step 8 — Launch EC2 instance**

In the AWS console:
- AMI: Ubuntu (same OS as local VM — familiar commands)
- Instance type: t3.micro (~$0.03/hour)
- Key pair: url-shortener-key.pem (required for SSH access, download and save safely)
- Storage: 16GB (8GB fills up quickly with Docker images)
- Security group: open port 22 (SSH) and port 5000 (Flask API)

**Step 9 — SSH into EC2**

    chmod 400 ~/Desktop/key-pairs/url-shortener-key.pem
    ssh -i ~/Desktop/key-pairs/url-shortener-key.pem ubuntu@<public-ip>

chmod 400 sets the key file to read-only for owner only — SSH refuses to 
use key files that other users can read, it's a security requirement.

EC2 is a brand new blank Ubuntu machine — nothing is installed. Every tool 
must be set up fresh just like any new computer.

**Step 10 — Install Docker and AWS CLI on EC2**

    sudo apt-get update
    sudo apt-get install -y docker.io
    sudo apt-get install -y docker-compose
    # Install AWS CLI
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    sudo apt-get install -y unzip
    unzip awscliv2.zip
    sudo ./aws/install

EC2 needs Docker to run containers and AWS CLI to authenticate with ECR. 
Every EC2 instance starts blank — this setup must be done each time you 
create a new instance. This is one of the problems CI/CD in Phase 5 solves.

**Step 11 — Configure AWS CLI on EC2 and authenticate Docker to ECR**

    aws configure  # same credentials as local machine
    aws ecr get-login-password --region us-west-1 | sudo docker login --username AWS --password-stdin 801498844513.dkr.ecr.us-west-1.amazonaws.com

EC2 is a completely separate machine — it doesn't inherit any configuration 
from your local machine. AWS CLI must be configured again with the same 
credentials so EC2 has permission to pull from ECR.

**Step 12 — Create docker-compose.yml and init.sql on EC2**

    nano docker-compose.yml
    nano init.sql

EC2 has no access to your local VS Code files. These files must be recreated 
manually on EC2. The key difference in the EC2 docker-compose.yml:

Local version uses:
    web:
      build: .   # builds image from local Dockerfile

EC2 version uses:
    web:
      image: 801498844513.dkr.ecr.us-west-1.amazonaws.com/url-shortener:latest

EC2 pulls the pre-built image from ECR instead of building from a Dockerfile 
since the Dockerfile and source code don't exist on EC2.

Also added healthcheck so Flask waits for MySQL to be fully ready:
    mysql-db:
      healthcheck:
        test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-ppassword"]
        interval: 10s
        timeout: 5s
        retries: 5
    web:
      depends_on:
        mysql-db:
          condition: service_healthy

**Step 13 — Open port 5000 in security group**

In AWS console → EC2 → Security Groups → Edit inbound rules → Add rule:
- Type: Custom TCP, Port: 5000, Source: 0.0.0.0/0

By default EC2 blocks all incoming traffic except SSH (port 22). Opening 
port 5000 allows public access to your Flask API. MySQL port 3306 stays 
closed — it only needs to communicate with Flask internally between 
containers. Exposing it publicly would be a security risk.

**Step 14 — Start containers**

    sudo docker compose up -d

Docker pulls Flask image from ECR, pulls MySQL from Docker Hub, starts both 
containers connected on the same network. App is now live.

### Verifying it works
Tested in Postman using the public EC2 IP:
- POST http://18.144.188.161:5000/shorten → returns short code, 200 OK
- GET http://18.144.188.161:5000/<short_code> → 302 redirect to original URL

### Understanding what "publicly accessible" means
The app is an API, not a website. Typing the IP in a browser shows 404 
because there's no route for /. The app is accessible to anything that 
can send HTTP requests — Postman, other apps, curl, or a frontend. 
A frontend (HTML/CSS/JS) would be what regular users interact with visually, 
but that's outside the scope of this project.

### Elastic IP
By default stopping and starting an EC2 instance assigns a new public IP. 
An Elastic IP is a static IP that stays the same across stop/start cycles.

    Allocated Elastic IP: 18.144.188.161

Note: Elastic IPs are free when associated with a running instance. When 
the instance is stopped the Elastic IP accumulates a small charge 
(~$0.005/hour). Terminate the instance and release the Elastic IP if 
no longer needed to avoid charges.

### Obstacles in Phase 4

**Obstacle 7 — SSH host key changed**
After stopping and restarting EC2, the host key changed causing SSH to 
refuse connection with "WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED". 
Fixed by clearing the old key:

    ssh-keygen -f '/home/justin/.ssh/known_hosts' -R '<old-ip>'

This happens because stopping EC2 can change the underlying host — the 
Elastic IP fixed the IP issue but the host key can still change.

**Obstacle 8 — EC2 disk space full**
Docker accumulated old images filling the 8GB disk to 100%. MySQL couldn't 
initialize because there was no space to write files. Fixed by:

    sudo docker system prune -a -f   # remove all unused Docker resources
    rm awscliv2.zip                  # remove installer zip
    rm -rf aws                       # remove installer folder

Then increased EC2 volume from 8GB to 16GB in AWS console and extended 
the filesystem:

    sudo growpart /dev/nvme0n1 1
    sudo resize2fs /dev/root

**Obstacle 9 — MySQL corrupted files after disk full**
After the disk was full MySQL left corrupted initialization files. On next 
startup MySQL refused to initialize: "data directory has files in it". 
Fixed by removing volumes for a clean slate:

    sudo docker compose down -v
    sudo docker compose up -d

The -v flag removes volumes along with containers giving MySQL a fresh 
start.

**Obstacle 10 — Flask starting before MySQL ready**
depends_on only waits for the MySQL container to start, not for MySQL 
itself to finish initializing. Flask would start, immediately try to 
connect to MySQL, and fail with "Lost connection to MySQL server". Fixed 
by adding a healthcheck that makes Flask wait until MySQL is actually 
ready to accept connections.

---

## Phase 5 - CI/CD with GitHub Actions

### What is CI/CD and why it matters
Without CI/CD, every time you make a change you have to manually:
- Run tests
- Build a new Docker image
- Push it to ECR
- SSH into EC2
- Pull the new image and restart containers

With CI/CD, merging to main triggers all of that automatically. You still 
control when things go to production by deciding when to merge — CI/CD 
just handles all the deployment work after that decision.

Important clarification: CI/CD doesn't automatically update the main branch. 
You still merge manually. What's automated is everything that happens after 
the merge.

### CI vs CD — the distinction
CI (Continuous Integration) — every push to main automatically runs your 
tests. Catches broken code before it reaches production.

CD (Continuous Deployment) — if tests pass, automatically deploys. Builds 
a new Docker image, pushes to ECR, SSHs into EC2, pulls the new image, 
restarts containers.

The full automated flow:
    You merge feature branch to main
        ↓
    GitHub Actions triggers automatically
        ↓
    CI: runs unit tests
        ↓
    Tests pass?
        ↓ Yes
    CD: builds new Docker image
        ↓
    Pushes image to ECR
        ↓
    SSHs into EC2
        ↓
    Pulls new image and restarts containers
        ↓
    Live app updated — no manual steps

### What are tests and why write them
Tests are separate code files that automatically verify your app works 
correctly. They don't live in main.py — they live in test_app.py. The test 
file never runs in production, only in the CI pipeline.

The question of what to test: verify the things you wrote, not the libraries 
you use since those are already tested. For this project:
- POST route returns a short code with 200 status
- GET route returns a 302 redirect to the correct URL

### Understanding unittest and mocking
unittest is Python's built in testing library. No installation needed — 
it comes with Python.

The challenge: tests need to run without a real MySQL database. The CI 
runner has no database. Solution: mock the database connection.

Mocking means temporarily replacing a real function with a fake one during 
testing. The real logic still runs — only the external dependency (database) 
gets swapped out. This is the industry standard approach.

    from unittest.mock import patch, MagicMock

    @patch('main.get_connection')          # replaces get_connection with a fake
    def test_post_route(self, mock_get_connection):
        mock_conn = MagicMock()            # fake connection object
        mock_get_connection.return_value = mock_conn  # fake returns fake conn
        mock_conn.cursor().fetchone.return_value = None  # no collision found

@patch temporarily replaces get_connection in main.py with a MagicMock. 
Before the test runs real function gets swapped out. After the test finishes 
real function is restored. MagicMock allows any method call on it without 
crashing — so cursor(), execute(), commit(), close() all just work silently.

The only value that needs to be explicitly set is fetchone() — it needs to 
return None so the collision check passes and shorten_url() continues to 
the INSERT.

### Why only fake get_connection and not shorten_url
The rule is: fake anything that talks to an external service. 
get_company() is the boundary between your code and MySQL. shorten_url() 
itself doesn't talk to anything external — it just calls get_connection() 
and does logic. So you fake the boundary, test the real logic.

### Understanding response.headers['Location']
When Flask calls redirect('https://www.google.com') it doesn't return the 
URL as text in the response body. It returns a 302 response with a Location 
header that tells the browser where to go. The URL lives in the header, not 
the body — that's the HTTP standard for redirects.

    self.assertIn('https://www.google.com', response.headers['Location'])

### The test file

    import unittest
    from main import app
    from unittest.mock import patch, MagicMock

    class TestApp(unittest.TestCase):
        def setUp(self):
            app.config['TESTING'] = True
            self.client = app.test_client()

        @patch('main.get_connection')
        def test_post_route(self, mock_get_connection):
            mock_conn = MagicMock()
            mock_get_connection.return_value = mock_conn
            mock_conn.cursor().fetchone.return_value = None

            response = self.client.post('/shorten', json={'url': 'https://www.google.com'})

            self.assertEqual(response.status_code, 200)
            response_text = response.data.decode('utf-8')
            self.assertEqual(len(response_text), 6)

        @patch('main.get_connection')
        def test_get_route(self, mock_get_connection):
            mock_conn = MagicMock()
            mock_get_connection.return_value = mock_conn
            mock_conn.cursor().fetchone.return_value = ('https://www.google.com',)

            response = self.client.get('/abc123')

            self.assertEqual(response.status_code, 302)
            self.assertIn('https://www.google.com', response.headers['Location'])

### GitHub Actions workflow file
Stored at .github/workflows/deploy.yml. This file defines the entire 
pipeline. GitHub reads it automatically on every push to main.

Structure:
- name — label shown in the Actions tab
- on: push: branches: [main] — trigger condition
- jobs — the work to do
- needs: test — deploy only runs if test passes
- runs-on: ubuntu-latest — GitHub spins up a fresh Ubuntu VM for each job

Each job runs on a separate fresh VM — neither job shares anything with 
the other. Both need their own checkout step to get the code.

    name: CI/CD Pipeline

    on:
      push:
        branches: [main]

    jobs:
      test:
        runs-on: ubuntu-latest
        steps:
          - name: Checkout repository code
            uses: actions/checkout@v4

          - name: Set up Python
            uses: actions/setup-python@v5
            with:
              python-version: '3.12'

          - name: Install dependencies
            run: pip install -r requirements.txt

          - name: Run tests
            run: python -m unittest test_app.py

      deploy:
        needs: test
        runs-on: ubuntu-latest
        steps:
          - name: Checkout code
            uses: actions/checkout@v4

          - name: Configure AWS credentials
            uses: aws-actions/configure-aws-credentials@v4
            with:
              aws-region: us-west-1
              aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
              aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}

          - name: Login to Amazon ECR
            id: login-ecr
            uses: aws-actions/amazon-ecr-login@v2

          - name: Build, tag, and push docker image to Amazon ECR
            env:
              REGISTRY: ${{ steps.login-ecr.outputs.registry }}
              REPOSITORY: url-shortener
              IMAGE_TAG: latest
            run: |
              docker build -t $REGISTRY/$REPOSITORY:$IMAGE_TAG .
              docker push $REGISTRY/$REPOSITORY:$IMAGE_TAG

          - name: SSH into EC2 and restart containers
            uses: appleboy/ssh-action@v1.0.0
            with:
              host: ${{ secrets.EC2_HOST }}
              username: ubuntu
              key: ${{ secrets.EC2_KEY }}
              script: |
                aws ecr get-login-password --region us-west-1 | sudo docker login --username AWS --password-stdin 801498844513.dkr.ecr.us-west-1.amazonaws.com
                sudo docker pull 801498844513.dkr.ecr.us-west-1.amazonaws.com/url-shortener:latest
                sudo docker compose down
                sudo docker compose up -d

### GitHub Secrets
Credentials the workflow needs are stored as GitHub Secrets — never in code. 
Stored under repo Settings → Secrets and variables → Actions.

Secrets used:
- AWS_ACCESS_KEY_ID — authenticates GitHub Actions to AWS
- AWS_SECRET_ACCESS_KEY — authenticates GitHub Actions to AWS
- EC2_HOST — the Elastic IP so the workflow knows which server to deploy to
- EC2_KEY — the private key that lets GitHub Actions SSH into EC2

${{ secrets.SECRET_NAME }} is how the workflow references them. The actual 
values are never visible in logs or code — substituted securely at runtime.

### Access keys vs OIDC
Two ways to authenticate GitHub Actions to AWS:

Access Keys (what we use) — static credentials stored in GitHub Secrets. 
Simpler to set up. Fine for learning projects.

OIDC (OpenID Connect) — no stored credentials. GitHub and AWS establish 
a trust relationship. GitHub gets a temporary token per workflow run. More 
secure, industry standard for production. Worth upgrading to later.

### Obstacle 11 — SSH key not found
First deploy attempt failed with "ssh: no key found". The EC2_KEY secret 
wasn't being read correctly — the .pem file contents weren't copied 
completely into GitHub Secrets. Fixed by re-adding the secret making sure 
to copy the entire file including the header and footer lines:

    -----BEGIN RSA PRIVATE KEY-----
    ...all content...
    -----END RSA PRIVATE KEY-----

### Obstacle 12 — Deploy job appeared stuck
Deploy job ran for over 5 minutes and appeared frozen. It was actually 
working — pulling the Docker image layer by layer, stopping old containers, 
initializing MySQL with the healthcheck, and starting Flask. The healthcheck 
makes Flask wait for MySQL to be fully ready before starting which adds time. 
Eventually all steps completed and the pipeline showed green.

# KUBECTL
The goal here is to refactor the project and incorporate kubectl

## Steps
1. Install kubectl
2. Verify kubectl
3. Install minikube
4. start my cluster
5. Confirm its running

-> 1. I have to download the latest stable kubectl binary and make it executable since this is my first time

-> 2. Run 'kubectl version --client' to confirm it installed correctly

-> 3. I have to download the minikube binary

-> 4. Run 'minikube start' which starts up a local single-node Kubernetes cluster using Docker as the driver

-> 5. Run 'kubectl get nodes'

## Terms to know

### Node
A node is just one machine - could be a physical server, VM or a cloud instance (EC2) - thats part of a Kubernetes cluster and actually runs your containers.

### Cluster
A cluster is a whole system: one or more nodes that are managed together as a single unit, plus a control plane - the "brain" that makes decisions (which node should run which Pod, whether something crashed and needs restarting, etc) so "cluster" = control plane + the nodes its managing

### Single-node
Single-node means that the entire cluster - control plane and the actual workload - running part lives on one machine instead of being spread across several. Thats where minikube comes in, gives you a miniature cluster where your one VM is pretending to be both the brain and the worker. Note that real production clusters almost always have multiple nodes (often across multiple physical machines or availability zones)

### Pod
The smallest unit Kubernetes manages. Almost always, one Pod = one running instance of your container (Ex, one instance of your Flask app). Pods are disposable - Kubernetes can kill and recreate them at any time, and they get a new internal IP each time that happens.

### Deployment
Manages a set of identical Pods for you. You declare "I want 3 replicas of my Flask app running" and the Deployments job is to make that true at all times. If a Pod crashes or gets deleted then Deployment notices and creates a replacement automatically. Essentially it self-heals and provides easy scaling. 

### Service
Gives your Pods (which are constantly changing) a stable network address. Since Pods get new IPs every time they're recreated, we can't just hardcode "talk to Pod at 10.0.0.5" - That IP may not exist in the next 5 minutes from now. A Service sits in front of a group of Pods, it gets a stable internal DNS name/IP, and load-balances incoming traffic across whichever Pods are currently alive.

### kubectl - general purpose tool
Installation is a one time case which then serves as a general-purpose tool. I would use this kubectl binary not just for this project but for every future Kubernetes project.

kubectl is the command-line client for talking to any kubernetes cluster. It itself doesn't run a cluster but it just sends API requests to whatever cluster it's currently pointed.

kubectl reads a config file (~/.kube/config) that tells it which cluster to talk to and how to authenticate.

### minikube - local-only, for learning/dev
minikube is specifically a tool for running a lightweight, single-node Kubernetes cluster on your own machine. Serves as a training-wheel tool that anyone learning k8s (kubernetes) uses. Not meant to be carried forward into actual production deployment.

Its whole purpose is local development and learning. This is so I can experiment with real Kubernetes objects (Pods, Deployments, Services) without needing cloud infrastructure or incurring AWS costs while i'm still learning the concepts.

Not meant for use in real production - nobody runs minikube for a real deployed app. When moving over to EKS later, minikube goes away and kubectl points at the EKS cluster instead. 

## Kubernetes Manifest
The "instructions" (YAML) that tells Kubernetes what we want to exist, and Kubernetes works to make reality match it. Manifest doesn't tell Kubernetes how to start a Pod. It tells Kubernetes (declarative) what the end result should look like and Kubernetes figures out how to make it. Essentially describing a desired state.

### Creating YAML Deployment
Deployment Manifest is meant for one component at a time. I'll need to create two separate YAML deployment files. One is for the Flask application. Second is deployment for MySQL. These are two distinct pieces that behave completely different.

1. Stateless web service (Flask, fine to run 3 identical copies)
2. Stateful database (MySQL, must stay as exactly one source of truth)

Why? It was noted earlier that MySQL runs as one truth, one persistent database. Scaling Flask shouldn't multiply our database. So it doesn't need multiple replicas the way Flask does. But deployment isn't just about scaling too many copies. Its actual job is "keep this desired state true". If the MySQL Pod were to crash or have an issue, the Deployment notices the actual state doesn't match the desired state (0 Pods running instead of 1) and automatically creates a replacement. Essentially without a Deployment managing it, a crashed MySQL container would just stay crashed, with nothing watching it.

### Building Manifest
1. Specify how many replicas (Pods) to run.
2. Which image each Pod should run

The image specified is the URI address of the image which is the ECR path we created earlier.


### AWS credentials
minikube is running as an isolated environment. Meaning it won't have our AWS credentials to authenticate against the private ECR repo we created. We need to give minikube AWS credential access to pull from ECR. This step will be worked on after creating the Kubernetes Manifest.
