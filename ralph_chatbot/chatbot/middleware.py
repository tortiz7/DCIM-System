import logging
import time
from django.conf import settings
from django.http import HttpResponseServerError
from prometheus_client import Counter, Histogram
from .api.metrics import MetricsCollector

logger = logging.getLogger(__name__)

# Define Prometheus metrics
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
    """
    Middleware for handling chatbot-specific request processing.
    Adds AI context, metrics collection, and error handling.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.metrics_collector = MetricsCollector()
        
        # Verify chatbot port configuration
        if not settings.CHATBOT_PORT == 8001:
            logger.warning(
                "Chatbot port is not configured to 8001. Current port: %s",
                settings.CHATBOT_PORT
            )

    async def __call__(self, request):
        # Start timing the request
        start_time = time.time()
        
        # Skip middleware for static files and health checks
        if request.path.startswith('/static/') or request.path == '/health/':
            return await self.get_response(request)

        try:
            # Add AI context to the request
            request.ai_context = await self.get_ai_context(request)
            
            # Add metrics context
            request.metrics = await self.get_metrics_context()
            
            # Process the request
            response = await self.get_response(request)
            
            # Record metrics
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
            AI_CONTEXT_ERRORS.inc()
            return HttpResponseServerError("Internal server error in chatbot middleware")

    async def get_ai_context(self, request):
        """
        Generate AI context for the request including:
        - User information
        - Previous interactions
        - System state
        """
        try:
            context = {
                'user_id': request.user.id if request.user.is_authenticated else None,
                'session_id': request.session.session_key,
                'previous_interactions': await self.get_previous_interactions(request),
                'system_metrics': await self.metrics_collector.get_relevant_metrics(
                    request.path
                ),
            }
            return context
        except Exception as e:
            logger.error(f"Error generating AI context: {str(e)}", exc_info=True)
            AI_CONTEXT_ERRORS.inc()
            return {}

    async def get_metrics_context(self):
        """
        Get current system metrics for request context
        """
        try:
            return await self.metrics_collector.get_all_metrics()
        except Exception as e:
            logger.error(f"Error collecting metrics: {str(e)}", exc_info=True)
            return {}

    async def get_previous_interactions(self, request):
        """
        Retrieve recent interaction history for the current user/session
        """
        # Get last 5 interactions from cache/db
        try:
            if request.user.is_authenticated:
                # Get user-specific interactions
                return await self.get_user_interactions(request.user.id)
            else:
                # Get session-based interactions
                return await self.get_session_interactions(request.session.session_key)
        except Exception as e:
            logger.error(
                f"Error retrieving interaction history: {str(e)}", 
                exc_info=True
            )
            return []

    async def get_user_interactions(self, user_id):
        """Get interactions for authenticated users"""
        # Implementation for getting user interactions from cache/db
        pass

    async def get_session_interactions(self, session_key):
        """Get interactions for anonymous sessions"""
        # Implementation for getting session interactions from cache/db
        pass

class MetricsMiddleware:
    """
    Additional middleware specifically for handling metrics collection
    and prometheus integration.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    async def __call__(self, request):
        try:
            response = await self.get_response(request)
            
            # Skip metrics for static files
            if not request.path.startswith('/static/'):
                self.record_metrics(request, response)
                
            return response
            
        except Exception as e:
            logger.error(f"Metrics middleware error: {str(e)}", exc_info=True)
            return HttpResponseServerError("Internal server error in metrics middleware")

    def record_metrics(self, request, response):
        """Record various metrics about the request/response cycle"""
        REQUEST_COUNT.labels(
            endpoint=request.path,
            status=response.status_code
        ).inc()