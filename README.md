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

    -git checkout -b (name-of-branch)
    -git branch

This is to create a new branch in the repo and git branch is what allows us to see which branch we're currently in.


### secrets string
To create true randomness when shortening URLs we import secrets as its designed for security and cryptography while random is meant to be used for modelling and simulaton.

## flask
Initialized flask then we have to create two routes.  
One route for POST which is going to receive a long URL and then returns a short code  
Second route for GET where it looks up the code and redirects to the long URL

The first route I'm assuming would be the route where it receives the user inputted URL which is the POST and then that route would then return the shortened URL back. The second URL would be the redirecting part when the user actually clicks the new shortened URL where if the route detects the short URL route then it redirects to the original long url website which would be the GET

## Challenges/Process

I first created a variable (alphabet) that contained random string values and numbers. Then created a function that when called returns a variable (short_url) with values containing 6 values of alphabet. Then created a while loop that checks if the newly short url already exists and if it does then reassign short url with the function call again. If it does not exist already then the code continues to where the dict is assigned the short url along with its long url partner. Refactored shorten code into one function which calls on create_short_url function.

### Obstacle 1 (POST request)
I had a challenging time understanding the POST request I was suppose to make.

    @app.route('/shorten', methods = ['POST'])
    def returns_short_url():
        long_url = request.get_json()
        long_url = long_url.get('url')
        new_short_url = shorten_url(long_url)
        return new_short_url

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