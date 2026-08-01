from rest_framework.throttling import AnonRateThrottle


class OTPResendThrottle(AnonRateThrottle):
    """Custom throttle rate for OTP resend request endpoint."""
    rate = "3/minute"
    scope = "otp_resend"
