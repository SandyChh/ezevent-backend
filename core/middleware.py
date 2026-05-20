"""
Security headers middleware.
Addresses the five medium-severity OWASP ZAP findings documented
in Section 5.7 of the report:
  - X-Content-Type-Options (handled by Django SECURE_CONTENT_TYPE_NOSNIFF)
  - Strict-Transport-Security (handled by Django SECURE_HSTS_SECONDS)
  - Content-Security-Policy (this middleware)
  - Referrer-Policy (handled by Django SECURE_REFERRER_POLICY)
  - Suppress verbose Server header (this middleware)
"""


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Content-Security-Policy — allow Stripe Elements iframe (Section 13)
        if "Content-Security-Policy" not in response:
            response["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' https://js.stripe.com; "
                "frame-src https://js.stripe.com; "
                "img-src 'self' data:; "
                "style-src 'self' 'unsafe-inline'; "
                "connect-src 'self' https://api.stripe.com"
            )

        # Suppress verbose Server header (ZAP finding)
        if "Server" in response:
            del response["Server"]

        return response
