# README

# url-shortener
A backend service that shortens URLs, stores them in a database, and 
redirects visitors. Built with Flask, MySQL, Docker, and deployed to AWS 
with a GitHub Actions CI/CD pipeline.

This project is primarily a learning exercise. Every phase was built 
bit by bit with the goal of understanding each piece before moving to 
the next. README shows the documentation and learning/thought process.

> See [NOTES.md](./NOTES.md) for the full phase-by-phase breakdown, 
> obstacles hit, and terms learned along the way.

---

## Goals
- Build a real backend service from scratch
- Learn Flask REST API design
- Learn MySQL database integration
- Learn Docker containerization
- Learn AWS deployment
- Learn CI/CD with GitHub Actions
- Learn Kubernetes orchestration

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
a real public URL accessible from anywhere on the internet. EC2 pulls the 
Flask image from ECR (Elastic Container Registry) and the MySQL image from 
Docker Hub, runs both containers, and serves the API publicly on port 5000.

### Phase 5 - CI/CD with GitHub Actions
A GitHub Actions workflow automatically triggers on every push to main. 
Tests run first — if they pass, a new Docker image is built, pushed to ECR, 
and EC2 automatically pulls and restarts with the updated version. You still 
merge to main manually — CI/CD automates everything that happens after.

### Phase 6 - Kubernetes
The Flask and MySQL containers are deployed as two separate Kubernetes 
Deployments (k8s/flask-deployment.yaml, k8s/mysql-deployment.yaml), each 
paired with its own Service. Flask runs as 3 replicas behind a NodePort 
Service, exposing the app outside the cluster. MySQL runs as 1 replica 
behind a ClusterIP Service, reachable only from inside the cluster — Flask 
connects to it by Service name (mysql-db) the same way it did in Docker 
Compose. A Secret authenticates image pulls from the private ECR repo, and 
a ConfigMap holds init.sql, mounted into the MySQL container to create the 
urls table on startup. Tested locally on minikube.

---

## Git Workflow
One branch per phase. Main always has stable working code. Never work 
directly on main.

    git checkout -b phase-name                     # create and switch to branch
    git branch                                     # see all branches, * = current
    git push --set-upstream origin phase-name      # first push of new branch
    git push                                       # subsequent pushes
    git checkout main && git merge phase-name      # merge completed phase


---

## Saved for Later
- Click tracking — log every redirect with timestamp, IP, user agent
- MySQL named volume — persist data across docker compose down locally
- AWS RDS — managed cloud database as single source of truth in production
- Move Flask to port 80/443 with Nginx as reverse proxy
- Add restart: always to docker-compose for auto-start on EC2 boot
- Upgrade authentication from access keys to OIDC for production security
- Deploy to real EKS instead of local minikube
- Add liveness/readiness probes to Deployments
- Add a Persistent Volume for MySQL so data survives Pod recreation
- Add resource requests/limits to containers