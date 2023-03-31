# Scoring API

TODO: test that cache is actually used if exists

This is a demo of a simple scoring API. The method of scoring and arguments for them are passed in the request's body. The focus of the demo is not on API itself, but rather on request's parameters validation using classes.

For demo purposes, parameters are passed as JSON dictionary inside  POST request.

## Python Features Summary
* Metaclasses
* Data descriptors
* Class inheritance
* Factories
* HTTPServer, POST requests, checking tokens

## Request Structure
* `account` - string, optional can be empty
* `login` - string, required, can be empty
* `token` - strin, required, can be empty
* `method` - string, required, can be empty
* `arguments` - dict (JSON object), required, can be empty

API invokes the corresponding scoring method, depending on `method` parameter. But before that it "authenticates" user using `account`, `login` and `token` parameters. If `login` = `admin` and the token is valid, it simply returns '42'.
In case of bad auth it returns:
* `{"code": 403, "error": "Forbidden"}`


## Scoring Methods Implemented
### online_score
Arguments:
* `phone` - string or number of len = 11, started with 7, optional, can be empty
* `email` - string of email pattern, optional, can be empty
* `first_name` - string, optional, can be empty
* `last_name` - string, optional, can be empty
* `birthday` - string with a pattern DD.MM.YYYY, less than 70 years behind current date, optional, can be empty
* `gender` - number 0, 1 or 2, optional, can be empty

Validation:
* Each argument has an appropriate field class, which validates value at time of assignment.
* Additionally, method ensures that at least 2 arguments (phone-email, first_name-last_name, or gender-birthday are non-empty)

Calls:
* `get_score` function in `scoring.py`

Result:
* `{"score": number}` with `code` = 200
* or `{"error": "Field descripton which caused error}` and code = 422
* As well, it adds `has` variable to context, as a list of non-empty arguments

### clients_interests
Arguments:
* `client_ids` - list of integers, required, not empty
* `date` - date string of a pattern DD.MM.YYYY, optional, can be empty

Validation:
* Each argument has an appropriate field class, which validates value at time of assignment.

Calls:
* `get_interests` function in `scoring.py`

Result:
* `{"id1": ["interest1", "interest2" ...], "id2": [...] ...}` with `code` = 200
* or `{"error": "Field descripton which caused error}` and code = 422
* As well, it adds `nclients` variable to context, with a number of ids in `client_ids`.

## Usage
### Run API and Invoke Requests
1. Either:
   1. Run main() from your Python IDE. This starts simple Python http.server, or
   2. Make sure your currend dir is one level up of `scoring_api` dir, and run from CLI `python -m scoring_api.api`. You may optionally specify port and log file location, like: `python -m scoring_api.api -p 8001 -l mylog.txt`
2. Invoke POST requests*, ** to the server, check responses:
* `$ curl -X POST -H "Content-Type: application/json" -d '{"account": "testacc", "login": "testlog", "method": "online_score", "token": "d0ffdbabce6b9ceb5f95127347a501c78d04592813ffbb4eae224ed18f838998e0ea214d382fab2a69712d433aab30259abd1f99734da71440dc270a99a5cbab", "arguments": {"phone":78888888888, "email": "test@mail.ent"}}' http://localhost:8080/method`

* `$ curl -X POST -H "Content-Type: application/json" -d '{"account": "testacc", "login": "testlog", "method": "clients_interests", "token": "d0ffdbabce6b9ceb5f95127347a501c78d04592813ffbb4eae224ed18f838998e0ea214d382fab2a69712d433aab30259abd1f99734da71440dc270a99a5cbab", "arguments": {"client_ids": [1, 2, 10, 25], "date": "22.03.1996"}}' http://localhost:8080/method`

\* If you are on Windows and have Git installed, use Git Bash (CLI-type app) to have an access to `curl` 
\** If you'd like to invoke requests from `admin` login, you should create correct token first, using the current date and time (hour), plus adding admin's salt (42):
* `hashlib.sha512('yyyymmddhh42'.encode()).hexdigest()`
... and use it as a `token` parameter with `login` = `admin`.

###Run Tests
* Make sure your currend dir is one level up of `scoring_api` dir, and run `python -m scoring_api.test`


+REDIS
docker run -d --name redis-stack-server -p 6379:6379 redis/redis-stack-server:latest
docker exec -it redis-stack-server redis-cli
