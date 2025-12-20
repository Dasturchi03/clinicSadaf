import os
from PIL import Image
from django.db import models
from django.utils.html import format_html
from rest_framework.exceptions import ValidationError


class BaseModel(models.Model):
    """Default fields for all models."""

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True


class BaseImageModel(BaseModel):
    class Meta:
        abstract = True

    def clean(self):
        super().clean()
        try:
            image = self.image
            size = image.size / (1024 * 1024)

            # Check if size more than 2MB
            if size > 2:
                raise ValidationError("Image size must be less than 2 MB.")

            img = Image.open(image)
            width, height = img.size

            # Check if dimensions match the required size
            if width != 1080 or height != 1440:
                raise ValidationError("Image dimensions must be 1080x1440 pixels.")

        except Exception as e:
            # Handle any exceptions that occur during the validation process
            raise ValidationError(f"Failed to validate image: {e}")

    def image_preview(self):
        # image preview is used for admin page
        return format_html('<img src="{}" style="max-height: 150px; max-width: 150px;" />'.format(self.image.url))

    def delete_photo(self):
        # remove file from storage if object was deleted

        if self.image:
            file_path = self.image.path
            if os.path.exists(file_path):
                os.remove(file_path)
