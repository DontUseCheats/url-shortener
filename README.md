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

### secrets string
To create true randomness when shortening URLs we import secrets as its designed for security and cryptography while random is meant to be used for modelling and simulaton.