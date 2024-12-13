import logging
import time
from django.conf import settings
from django.http import HttpResponseServerError
from prometheus_client import Counter, Histogram
from .api.metrics import MetricsCollector

logger = logging.getLogger(__name__)

REQUEST_LATENCY = Histogram(
    'chatbot_request_latency_seconds',
    'Request latency in seconds',
    ['endpoint']
)
REQUEST_COUNT = Counter(
    'chatbot_request_total',
    'Total number of requests',
    ['endpoint', 'status']
)
AI_CONTEXT_ERRORS = Counter(
    'chatbot_ai_context_errors_total',
    'Total number of AI context generation errors'
)

class ChatbotMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.metrics_collector = MetricsCollector()

    def __call__(self, request):
        start_time = time.time()

        # Skip middleware for static files and health checks
        if request.path.startswith('/static/') or request.path == '/health/':
            return self.get_response(request)

        try:
            # Add mock metrics to request context
            request.metrics = self.metrics_collector.get_all_metrics()
            
            # Add AI context with mock data
            request.ai_context = {
                'system_metrics': request.metrics,
                'session_id': request.session.session_key or 'mock_session',
                'previous_interactions': []  # Could be enhanced with mock interactions
            }

            response = self.get_response(request)

            REQUEST_COUNT.labels(
                endpoint=request.path,
                status=response.status_code
            ).inc()

            REQUEST_LATENCY.labels(
                endpoint=request.path
            ).observe(time.time() - start_time)

            return response

        except Exception as e:
            logger.error(f"Middleware error: {str(e)}", exc_info=True)
            return HttpResponseServerError("Internal server error")

    def get_ai_context(self, request):
        try:
            context = {
                'user_id': request.user.id if request.user.is_authenticated else None,
                'session_id': request.session.session_key,
                'previous_interactions': self.get_previous_interactions(request),
                'system_metrics': self.metrics_collector.get_relevant_metrics(request.path),
            }
            return context
        except Exception as e:
            logger.error(f"Error generating AI context: {str(e)}", exc_info=True)
            AI_CONTEXT_ERRORS.inc()
            return {}

    def get_metrics_context(self):
        try:
            return self.metrics_collector.get_all_metrics()
        except Exception as e:
            logger.error(f"Error collecting metrics: {str(e)}", exc_info=True)
            return {}

    def get_previous_interactions(self, request):
        try:
            if request.user.is_authenticated:
                return self.get_user_interactions(request.user.id)
            else:
                return self.get_session_interactions(request.session.session_key)
        except Exception as e:
            logger.error(f"Error retrieving interaction history: {str(e)}", exc_info=True)
            return []

    def get_user_interactions(self, user_id):
        # Implement user interactions retrieval
        return []

    def get_session_interactions(self, session_key):
        # Implement session interactions retrieval
        return []

class MetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            if not request.path.startswith('/static/'):
                REQUEST_COUNT.labels(
                    endpoint=request.path,
                    status=response.status_code
                ).inc()
            return response
        except Exception as e:
            logger.error(f"Metrics middleware error: {str(e)}", exc_info=True)
            return HttpResponseServerError("Internal server error in metrics middleware")
