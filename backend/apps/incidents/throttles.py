from rest_framework.throttling import SimpleRateThrottle

class PublicIncidentIPRateThrottle(SimpleRateThrottle):
    scope = 'public_incident_ip'

    def get_rate(self):
        return '5/hour'

    def get_cache_key(self, request, view):
        return f"throttle_ip_{self.get_ident(request)}"

class PublicIncidentQRRateThrottle(SimpleRateThrottle):
    scope = 'public_incident_qr'

    def get_rate(self):
        return '3/10m'

    def parse_rate(self, rate):
        # 3 per 10 minutes (600 seconds)
        return (3, 600)

    def get_cache_key(self, request, view):
        qr_identifier = view.kwargs.get('code_identifier', '')
        if not qr_identifier:
            return None
        return f"throttle_qr_{qr_identifier}"
