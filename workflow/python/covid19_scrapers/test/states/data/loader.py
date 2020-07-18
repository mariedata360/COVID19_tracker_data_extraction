import inspect
import json
from pathlib import Path

import jinja2
import pandas as pd


def get_csv(csv_file, **kwargs):
    current_file = inspect.getfile(get_csv)
    template_path = Path('/'.join(current_file.split('/')[:-1] + ['csv']))
    csv_path = Path(csv_file)
    full_path = template_path.joinpath(csv_path)
    return pd.read_csv(str(full_path), **kwargs)


def get_template(template_name):
    current_file = inspect.getfile(get_template)
    template_path = '/'.join(current_file.split('/')[:-1] + ['templates'])
    _loader = jinja2.FileSystemLoader(searchpath=template_path)
    _env = jinja2.Environment(loader=_loader, autoescape=True)
    return _env.get_template(template_name)


def get_json(file_name):
    current_file = inspect.getfile(get_json)
    base_path = Path('/'.join(current_file.split('/')[:-1] + ['json']))
    json_path = Path(file_name)
    with base_path.joinpath(json_path).open() as json_file:
        return json.loads(json_file.read(), object_hook=try_keys_to_int)


def try_keys_to_int(d):
    try:
        return {int(k): v for k, v in d.items()}
    except ValueError:
        return d
