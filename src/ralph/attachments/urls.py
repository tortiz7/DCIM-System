from django.urls import re_path as url

from ralph.attachments.views import ServeAttachment

urlpatterns = [
    url(
        r'^attachment/(?P<id>\d+)-(?P<filename>.+)',
        ServeAttachment.as_view(),
        name='serve_attachment'
    ),
]
