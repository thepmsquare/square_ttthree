"""
all user-facing api response messages should be defined in this file
and paired with the `get_api_output_in_standard_format` function from
`square_commons` using the `message` parameter.
"""

messages = {
    "CREATE_SUCCESSFUL": "the record has been created successfully.",
    "READ_SUCCESSFUL": "the record has been retrieved successfully.",
    "UPDATE_SUCCESSFUL": "the record has been updated successfully.",
    "DELETE_SUCCESSFUL": "the record has been deleted successfully.",
    "GENERIC_204": "no content available for the requested resource.",
    "GENERIC_400": "the request is invalid or cannot be processed.",
    "GENERIC_500": "an internal server error occurred. please try again later.",
    "GENERIC_404": "the record could not be found.",
}

