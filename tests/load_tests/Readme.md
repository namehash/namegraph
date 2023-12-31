# Load testing

## Install locust

```
pip install locust
```
or using Poetry
```
poetry run pip install locust
```

## Run test

In source file `locust_suggestions_by_category.py` time between requests per user is defined as random number between 1 and 5:
```python
class WebsiteUser(HttpUser):
    wait_time = between(1, 5)
```

Run test with maximum number of 20 users, new user spawning rate 0.1 per second.

```
poetry run locust -f locust_suggestions_by_category.py --users 20 --spawn-rate 0.1 --autostart -t 5m -H "http://54.89.196.85"
```

## Tests

`run_tests.sh` runs load tests with 1 2 3 4 6 8 16 32 parallel users, between time is set to 0.
Tests are made from NameGenerator docker container and logs are saved in `reports` directory.

```commandline
apt update
apt install vim htop
pip3 install locust

bash run_tests.sh > log 2>&1
```

Memory with number of workers:
- uvicorn 1 5 GB
- uvicorn 2 9 GB
- uvicorn 4 13 GB
- uvicorn 8 31 GB? crash
- gunicorn 4 with preload 8 GB
- gunicorn 8 with preload 11 GB

Conclusions:
- more workers is better, probably more than 2 x vCPU will be better because ES is taking long time
- more workers needs more RAM, we can try more initialization on startup or focus on memory optimization
- with 4 vCPU nad 8GB RAM we can serve 934 requests for 4 parallel users in 1 minute with avg time 248 ms
- with 4 vCPU nad 11GB RAM we can serve 1383 requests for 6 parallel users in 1 minute with avg time 247 ms

apt update
apt install curl vim htop
pip3 install locust
vim run_tests.sh 
vim locust_suggestions_by_category.py


bash run_tests.sh > log 2>&1



poetry run gunicorn web_api:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --timeout 120

Memory worker (VIRT, RES):
- uvicorn 1: 5,5GB 4GB  14.8-11=3.8 GB
- uvicorn 2: 2x 5,5GB 4GB 18.7-11=7.7 GB
- gunicorn 1 worker sync: 15.1-11.3=3.8 GB
- gunicorn 2 worker sync: 19.1-11.4=7.7 GB
- gunicorn 2 worker uvicorn with preload: 15.6-11.7 = 3.9 GB
- gunicorn 4 worker uvicorn with preload: 4 GB
- gunicorn 8 worker uvicorn with preload: 11 GB