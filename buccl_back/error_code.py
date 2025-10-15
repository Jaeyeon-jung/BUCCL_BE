class ErrorCode:
    AUTHORIZATION_HEADER_MISSING = {"code": "1001", "message": "로그인해 주세요."}
    TOKEN_EXPIRED = {"code": "1002", "message": "세션이 만료되었습니다. 다시 로그인해주세요."}
    INVALID_TOKEN = {"code": "1003", "message": "Invalid token"}
    MISSING_REQUIRED_FIELD = {"code": "1004", "message": "Missing required field"}
    ALREADY_REGISTERED = {"code": "1005", "message": "이미 등록되어 있습니다."}
    GENERAL_ERROR = {"code": "1006", "message": "An error occurred"}
