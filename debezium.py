import requests
import json

class DebeziumConnector:
    def __init__(self, url):
        self.url = url

    def create_connector(self, name, transforms):
        headers = {'Content-Type': 'application/json'}
        config = {
            "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
            "database.hostname": "postgres",
            "database.port": 5432,
            "database.user": "postgres",
            "database.password": "postgres",
            "database.dbname": "postgres",
            "database.server.name": "postgres",
            "table.include.list": "public.events",
            "topic.prefix": "outbox"
        }
        payload = {"name": name, "config": config | transforms}
        response = requests.post(self.url, headers=headers, data=json.dumps(payload))
        return response.json()
