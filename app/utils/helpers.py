from flask import jsonify

def api_success(data=None, message=None, status_code=200):
    """
    Format consistent API success response:
    {
       "success": true,
       "data": ...,
       "message": ...
    }
    """
    response = {
        "success": True,
        "data": data or {},
        "message": message or "Request processed successfully."
    }
    return jsonify(response), status_code

def api_error(code, message, status_code=400):
    """
    Format consistent API error response:
    {
       "success": false,
       "error": {
          "code": ...,
          "message": ...
       }
    }
    """
    response = {
        "success": False,
        "error": {
            "code": code,
            "message": message
        }
    }
    return jsonify(response), status_code
