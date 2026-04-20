from exceptions.main_exception import BitPulseException


class AlertNotFoundException(BitPulseException):
    def __init__(self):
        self.message = "Alert not found in database. Try to create this alert first."
        self.status_code = 404


class AlertPriceTresholdValidateException(BitPulseException):
    def __init__(self, message: str):
        self.message = message
        self.status_code = 400


class AlertUnexpectedStatusException(BitPulseException):
    def __init__(self, status: str):
        self.message = f"Unexpected alert status: {status}"
        self.status_code = 400


class AlertNotificationAlreadyEnabledException(BitPulseException):
    def __init__(self):
        self.message = "Alert notification is already enabled."
        self.status_code = 400
