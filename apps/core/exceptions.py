import logging
from django.http.response import Http404
from django.db import IntegrityError
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    ValidationError,
)
from rest_framework.exceptions import ErrorDetail, NotFound
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied
from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class UniqueValidationError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Unique constraint violation.")
    default_code = "unique"
    

class BaseException(APIException):
    status_code = 400
    
    def __init__(self, error_message: str = None):
        detail: dict = {
            "error": {
                "error_message": error_message
            }
        }
        self.detail = detail


class MethodNotFound(BaseException):
    status_code = 400
    error_message = 'Method not found!'
    
    
class SerializerNotFound(Exception):
    pass

class ModuleNotFound(Exception):
    pass

logger = logging.getLogger(__name__)


AUTH_EXCEPTIONS = (
    AuthenticationFailed,
    NotAuthenticated,
    InvalidToken,
    TokenError,
)


def custom_exception_handler(exc, context):
    if isinstance(exc, Http404):
        exc = NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = DRFPermissionDenied()
    elif isinstance(exc, IntegrityError):
        if not settings.DEBUG:
            exc = ValidationError(_("A database error occurred, please try again later."))
        else:
            exc = ValidationError(set(exc.args))

    response = exception_handler(exc, context)
    # The response for this custom exception is already formatted
    if isinstance(exc, UniqueValidationError):
        return response

    if response is not None:
        status_code = response.status_code

        if isinstance(exc, AUTH_EXCEPTIONS):
            status_code = status.HTTP_401_UNAUTHORIZED

        # Check if the error details are in dictionary format and recursively process them
        if hasattr(exc, "detail"):
            if isinstance(exc.detail, (list, dict)):
                formatted_detail = process_error_detail(exc.detail)
            else:
                formatted_detail = str(exc.detail)
        else:
            formatted_detail = "An unknown error occurred."

        formatted_data = {"status_code": status_code, "detail": formatted_detail}

        return Response(formatted_data, status=status_code, headers=response.headers)

    return response


def process_error_detail(detail):
    """
    Recursively processes error details to format them according to a custom specification.
    This version handles the deepest nested errors differently, placing the error message
    directly if it's the deepest level.
    """
    if isinstance(detail, dict):
        details = []
        for field, errors in detail.items():
            if isinstance(errors, list):
                # Process list of errors
                field_errors = process_list_errors(errors)
                if len(field_errors) == 1 and isinstance(field_errors[0], str):
                    # If there is only one error and it is a string, place it directly
                    details.append({"field_name": field, "errors": field_errors[0]})
                else:
                    details.append({"field_name": field, "errors": field_errors})
            elif isinstance(errors, ErrorDetail):
                details.append({"field_name": field, "errors": str(errors)})
            elif isinstance(errors, dict):
                # Recursive call for nested dictionaries
                nested_errors = process_error_detail(errors)
                details.append({"field_name": field, "errors": nested_errors})
            else:
                details.append({"field_name": field, "errors": str(errors)})
        return details
    elif isinstance(detail, list):
        return process_list_errors(detail)
    else:
        # Single non-dictionary errors, treated as a simple error message
        return str(detail)


def process_list_errors(errors):
    """
    Helper function to process a list of errors and determine how to present them
    based on their depth and content.
    """
    result_errors = []
    for error in errors:
        if isinstance(error, ErrorDetail):
            result_errors.append(str(error))
        elif isinstance(error, dict):
            # Recursive call to process nested dictionaries
            nested_errors = process_error_detail(error)
            if (
                len(nested_errors) == 1
                and "errors" in nested_errors[0]
                and isinstance(nested_errors[0]["errors"], str)
            ):
                # Flatten the structure if it's the deepest error
                result_errors.append(nested_errors[0]["errors"])
            else:
                result_errors.extend(nested_errors)
        else:
            result_errors.append(str(error))
    return result_errors
