from typing import List, Sequence
from flask import Flask, request

temperatures = []
app = Flask(__name__)


def get_temperature_values() -> List[float]:
    return [el['temperature'] for el in temperatures]


def get_temperatures_variance(data: Sequence[float]) -> float:
    n = len(data)

    mean = sum(data) / n

    squared_diff = [(value - mean) ** 2 for value in data]

    return sum(squared_diff) / n


@app.route("/", methods=["GET"])
def get_temperatures():
    return temperatures


@app.route("/", methods=["POST"])
def add_temperature():
    body = request.json

    print(body)

    if body:
        temperatures.append(body["temperature_data"])

    return temperatures


@app.route("/batch", methods=["POST"])
def add_temperatures():
    body = request.json

    print(body)

    if body:
        temperatures.extend(body["temperatures_batch"])

    return temperatures


if __name__ == "__main__":
    app.run()
