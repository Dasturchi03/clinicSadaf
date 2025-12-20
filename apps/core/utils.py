from uuid import UUID
from datetime import datetime, date
from datetime import time
from django.db.models.fields.files import ImageFieldFile


def dict_for_formdata(input_dict: dict, list_files:bool = False):
    """
    Recursively flattens nested dict() for passing as form data
    source: https://stackoverflow.com/questions/76438291/drf-formdata-with-file-and-nested-array-of-objects-not-taking-nested-array-of-ob
    """
    results = {}
    stack = [((), input_dict)]

    while stack:
        path, current = stack.pop()
        for k, v in current.items():
            
            new_key = path + (k,)
            if isinstance(v, dict):
                stack.append((new_key, v))
            elif isinstance(v, (list, tuple, set)):
                for i, item in enumerate(v):
                    stack.append((new_key + (i,), item))
            elif hasattr(v, 'read'):
                if list_files:
                    results[".".join(new_key)] = [v]
                else:
                    results[".".join(new_key)] = v
            elif v == '':
                pass
            else:
                results[".".join(new_key)] = v
    return results

    
def json_datetime_serializer(obj):
    if isinstance(obj, (datetime, date)):
        serial = obj.isoformat()
        return serial

    if isinstance(obj, time):
        serial = obj.strftime('%H:%M')
        return serial

    if isinstance(obj, UUID):
        return str(obj)

    if isinstance(obj, ImageFieldFile):
        try:
            return obj.path
        except ValueError:
            return ''
    raise TypeError("{} is not JSON serializable.".format(obj))