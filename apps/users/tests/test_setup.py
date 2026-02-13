from rest_framework.test import APITestCase
from apps.users.models import User


class TestSetup(APITestCase):
    def __init__(self, methodName = "runTest"):
        self.urls = {
            'signup':'/api/users/signup',
            'login': '/api/users/login',
            'read': '/api/users/',
            'update': '/api/users/update',
            'delete': '/api/users/delete',
            'password-forgot': '/api/users/password-forgot',
            'password-reset': '/api/users/password-reset',
            'token-refresh': '/api/users/token/refresh',
        }
        
        super().__init__(methodName)
    
    def setUp(self):
        self.client.credentials(HTTP_X_API_VERSION='1.0')
        return super().setUp()

    def tearDown(self):
        return super().tearDown()