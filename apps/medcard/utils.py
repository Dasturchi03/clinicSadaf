import os
import uuid


def x_ray_uuid_path(instance, filename):
    ext = filename.split(".")[-1]
    new_filename = f"{uuid.uuid4()}.{ext}"
    # Define the path where the file will be uploaded
    return os.path.join("x_ray/", new_filename)
