class ClusterNotFoundException(Exception):
    pass

class UnSupportedPlatformException(Exception):
    pass

class UnsupportedOSType(Exception):
    pass

class ClientDownloadError(Exception):
    pass

class PullSecretNotFoundException(Exception):
    pass

class EmailPasswordNotFoundException(Exception):
    pass

class ResourceNameNotSpecifiedException(Exception):
    pass

class ResourceWrongStatusException(Exception):
    pass

class ResourceNotFoundError(Exception):
    pass

class TimeoutExpiredError(Exception):
    pass

class CommandFailed(Exception):
    pass

class NoInstallPlanForApproveFoundException(Exception):
    pass

class UnknownCloneTypeException(Exception):
    pass

class CSVNotFound(Exception):
    pass

class ChannelNotFound(Exception):
    pass

class DRPrimaryNotFoundException(Exception):
    pass