from locust import HttpUser, between, task


class WebsiteUser(HttpUser):
    wait_time = between(1, 5)

    URL = "/"

    @task(5)
    def instant(self):
        self.client.post(self.URL, name='instant', json={
            'name': 'string',
            'min_suggestions': 3,
            'max_suggestions': 3,
            "min_primary_fraction": 1.0,
            "params": {
                'conservative': True,
                'country': 'pl'
            }})

    @task(2)
    def domain_detail(self):
        self.client.post(self.URL, name='domain_detail', json={
            'name': 'string',
            'min_suggestions': 5,
            'max_suggestions': 5,
            "min_primary_fraction": 0.3,
            "params": {
                'conservative': True,
                'country': 'pl'
            }})

    @task(1)
    def full(self):
        self.client.post(self.URL, name='full', json={
            'name': 'string',
            'min_suggestions': 100,
            'max_suggestions': 100,
            "min_primary_fraction": 0.3,
            "params": {
                'conservative': False,
                'country': 'pl'
            }})
