from rest_framework.throttling import SimpleRateThrottle


class PublicQRScanRateThrottle(SimpleRateThrottle):
    scope = 'public_qr_scan'

    def get_cache_key(self, request, view):
        return f"throttle_qr_scan_{self.get_ident(request)}"

