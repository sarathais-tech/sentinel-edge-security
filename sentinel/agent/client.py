import requests


SERVER_URL = "http://127.0.0.1:8000/api/v1/metrics"


def send_metrics(metrics):
    try:
        response = requests.post(
            SERVER_URL,
            json=metrics,
            timeout=5,
        )

        response.raise_for_status()

        return {
            "success": True,
            "status_code": response.status_code,
            "response": response.json(),
        }

    except requests.RequestException as error:
        return {
            "success": False,
            "error": str(error),
        }