import csv
from functools import wraps
from rfc3339_validator import validate_rfc3339
from typing import Callable, List, Sequence, TypedDict, Union
from flask import Flask, jsonify, request
from jsonschema import validate, ValidationError

DATA_CSV = 'temperature_data.csv'


class TemperatureData(TypedDict):
    temperature: float
    time: str


def save_temperature_data_to_csv(temperature_data: Sequence[TemperatureData], filename: str = DATA_CSV):
    with open(filename, 'w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=['temperature', 'time'])

        writer.writeheader()

        writer.writerows(temperature_data)


def append_temperature_data_to_csv(temperature_data: Sequence[TemperatureData], filename: str = DATA_CSV):
    with open(filename, 'a', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=['temperature', 'time'])

        writer.writerows(temperature_data)


def read_temperature_data_from_csv(filename: str = DATA_CSV) -> List[TemperatureData]:
    temperature_data = []

    with open(filename, 'r') as csv_file:
        reader = csv.DictReader(csv_file)

        for row in reader:
            temperature_data.append({"temperature": float(
                row["temperature"]), "time": row["time"]})

    return temperature_data


def read_first_temperature_data_from_csv(filename: str = DATA_CSV) -> Union[TemperatureData, None]:
    first_temperature_data = None

    with open(filename, 'r') as csv_file:
        reader = csv.DictReader(csv_file)

        first_row = next(reader)

        first_temperature_data = TemperatureData({"temperature": float(
            first_row["temperature"]), "time": first_row["time"]})

    return first_temperature_data


def get_temperature_data() -> List[TemperatureData]:
    return read_temperature_data_from_csv()


def append_temperature_data(temperature_data: Sequence[TemperatureData]):
    existing_temperature_data = read_first_temperature_data_from_csv()

    if not existing_temperature_data:
        save_temperature_data_to_csv(temperature_data)
    else:
        append_temperature_data_to_csv(temperature_data)


def get_temperature_values(temperature_data: Sequence[TemperatureData]) -> List[float]:
    return [el['temperature'] for el in temperature_data]


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


def filter_temperatures(temperature_data: Sequence[TemperatureData]):
    values = get_temperature_values(temperature_data)

    mean = get_data_mean(values)

    sigma = get_data_sigma(values)

    filtered_temperatures = [el for el in temperature_data if mean -
                             3 * sigma <= el['temperature'] <= mean + 3 * sigma]

    return filtered_temperatures


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
    return get_temperature_data()


@app.route("/", methods=["POST"])
@route_wrapper(temperatureDataSchema)
def add_temperature():
    body = request.json

    if body:
        filtered_temperatures = filter_temperatures([body["temperature_data"]])

        if len(filtered_temperatures):
            append_temperature_data(filtered_temperatures)

        return filtered_temperatures


@app.route("/batch", methods=["POST"])
@route_wrapper(temperatureDataBatchSchema)
def add_temperatures():
    body = request.json

    # print(body)

    if body:
        filtered_temperatures = filter_temperatures(body["temperatures_batch"])

        if len(filtered_temperatures):
            append_temperature_data(filtered_temperatures)

        return filtered_temperatures


if __name__ == "__main__":
    app.run()
