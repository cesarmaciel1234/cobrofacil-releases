import requests

class MPApiClient:
    @staticmethod
    def get_headers(token, json_content=True):
        headers = {"Authorization": f"Bearer {token}"}
        if json_content:
            headers["Content-Type"] = "application/json"
        return headers

    @staticmethod
    def post(url, payload, token, timeout=10):
        return requests.post(url, json=payload, headers=MPApiClient.get_headers(token), timeout=timeout)

    @staticmethod
    def put(url, payload, token, timeout=10):
        return requests.put(url, json=payload, headers=MPApiClient.get_headers(token), timeout=timeout)

    @staticmethod
    def get(url, token, timeout=10):
        return requests.get(url, headers=MPApiClient.get_headers(token, False), timeout=timeout)

    @staticmethod
    def delete(url, token, timeout=5):
        return requests.delete(url, headers=MPApiClient.get_headers(token, False), timeout=timeout)
