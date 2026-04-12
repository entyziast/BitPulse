from exceptions.main_exception import BitPulseException


class ForbiddenUserException(BitPulseException):
    def __init__(self):
        self.message = "Forbidden user! You don't have access to this resource."
        self.status_code = 403


class UserNotFoundException(BitPulseException):
    def __init__(self):
        self.message = "User not found in database. Try to register first."
        self.status_code = 404

    
class UserAlreadyExistException(BitPulseException):
    def __init__(self):
        self.message = "User with this username already exist in database. Try to register with another username."
        self.status_code = 409


class UserWrongPasswordException(BitPulseException):
    def __init__(self):
        self.message = "Wrong password or username! Try to enter correct credentials."
        self.status_code = 401


class UserErrorToUpdateRefreshTokenException(BitPulseException):
    def __init__(self, username: str):
        self.message = f"Error to update refresh token for user with username '{username}'."
        self.status_code = 500