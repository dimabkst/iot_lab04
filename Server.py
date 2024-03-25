from functools import wraps
from rfc3339_validator import validate_rfc3339
from typing import Callable, List, Sequence, TypedDict, Union
from flask import Flask, jsonify, request
from jsonschema import validate, ValidationError


class TemperatureData(TypedDict):
    temperature: float
    time: str


temperatures: List[TemperatureData] = []


def get_temperature_values() -> List[float]:
    return [el['temperature'] for el in temperatures]


def get_data_mean(data: Sequence[float]) -> float:
    n = len(data)

    mean = sum(data) / n

    return mean


def get_data_variance(data: Sequence[float], mean: Union[float, None] = None) -> float:
    mean = mean or get_data_mean(data)

    n = len(data)

    squared_diff = [(value - mean) ** 2 for value in data]

    return sum(squared_diff) / n


def get_data_sigma(data: Sequence[float], variance: Union[float, None] = None) -> float:
    variance = variance or get_data_variance(data)

    return variance ** 0.5


def filter_temperatures():
    global temperatures

    data = get_temperature_values()

    mean = get_data_mean(data)

    sigma = get_data_sigma(data)

    temperatures = [el for el in temperatures if mean -
                    3 * sigma <= el['temperature'] <= mean + 3 * sigma]


class HttpError(Exception):
    def __init__(self, error_code: int = 500, message: str = "Something went wrong"):
        self.error_code = error_code

        self.message = message

        super().__init__(self.message)


temperatureDataSchema = {
    'type': 'object',
    'properties': {
            'temperature': {'type': 'number'},
            'time': {'type': 'string', 'format': 'date-time', "format_checker": validate_rfc3339}
    },
    'required': ['temperature', 'time']
}

temperatureDataBatchSchema = {
    'type': 'object',
    'properties': {
        'temperatures_batch': {
            'type': 'array',
            'items': temperatureDataSchema
        }
    },
    'required': ['temperatures_batch']
}


def validate_json(data, schema):
    try:
        validate(data, schema)

        return True, None
    except ValidationError as e:
        return False, e.message


def validate_route(json_schema):
    if json_schema:
        request_data = request.json

        is_valid, error_message = validate_json(request_data, json_schema)

        if not is_valid:
            raise HttpError(422, error_message or 'Validation error')


def route_wrapper(schema=None):
    def decorator(handler: Callable):
        @wraps(handler)
        def wrapper(*args, **kwargs):
            try:
                validate_route(schema)

                return handler(*args, **kwargs)
            except Exception as e:
                http_error = e if isinstance(e, HttpError) else HttpError()

                message, error_code = http_error.message, http_error.error_code

                print(f'Error: {e}. Code: {error_code}. Message: {message}')

                return jsonify({"error": message}), error_code
        return wrapper
    return decorator


app = Flask(__name__)


@app.route("/", methods=["GET"])
@route_wrapper()
def get_temperatures():
    return temperatures


@app.route("/", methods=["POST"])
@route_wrapper(temperatureDataSchema)
def add_temperature():
    body = request.json

    if body:
        temperatures.append(body["temperature_data"])

        filter_temperatures()

    return temperatures


@app.route("/batch", methods=["POST"])
@route_wrapper(temperatureDataBatchSchema)
def add_temperatures():
    body = request.json

    # print(body)

    if body:
        temperatures.extend(body["temperatures_batch"])

        filter_temperatures()

    return temperatures


if __name__ == "__main__":
    app.run()
