import traceback
from werkzeug.wsgi import ClosingIterator


import json, ast
from pusher_push_notifications import PushNotifications

class AfterResponse:
    def __init__(self, app=None):
        self.callbacks = []
        if app:
            self.init_app(app)

    def __call__(self, callback):
        self.callbacks.append(callback)
        return callback

    def init_app(self, app):
        # install extension
        app.after_response = self

        # install middleware
        app.wsgi_app = AfterResponseMiddleware(app.wsgi_app, self)

    def flush(self):
        for fn in self.callbacks:
            try:
                fn()
            except Exception:
                traceback.print_exc()

class AfterResponseMiddleware:
    def __init__(self, application, after_response_ext):
        self.application = application
        self.after_response_ext = after_response_ext

    def __call__(self, environ, after_response):
        iterator = self.application(environ, after_response)
        try:
            return ClosingIterator(iterator, [self.after_response_ext.flush])
        except Exception:
            traceback.print_exc()
            return iterator


def send_push(name, time):
    
    beams_client = PushNotifications(
        instance_id='97bc1b7f-aa2a-4760-af68-3052371c6dbd',
        secret_key='17482EE2588EE046FBA7E20949EBB4CE00AA2325E6FCDDCD3E34202E0A79A5CB',
    )
    
    response = beams_client.publish_to_interests(
        interests=['hello'],
        publish_body={
            'apns': {
                'aps': {
                    'alert': 'Hello!'
                }
            },
            'fcm': {
                'notification': {
                    'title': 'New access request',
                    'body': name + " has been requested to open at " + time
                }
            }
        }
    )

    print(response['publishId'])