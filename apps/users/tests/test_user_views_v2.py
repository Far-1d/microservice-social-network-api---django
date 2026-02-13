from .test_setup import  TestSetup
from apps.users.tests.factory import UserFactory, PasswordCodeFactory
from rest_framework import status
from apps.users.models import User
from apps.profiles.models import Profile, ProfilePrivacy
from django.utils.text import slugify
from django.utils import timezone
import os, json, time, redis
from dotenv import load_dotenv
import threading
from unittest import skip

load_dotenv()

@skip
class TestSignupView(TestSetup):
    def setUp(self):
        self.client.credentials(HTTP_X_API_VERSION='2.0')
 
        self.user_data = {
            'username': 'test 1001',
            'email': 'test.1001@gmail.com',
            'password': 'TestAb@1#'
        }
        self.whitespace_user_data = {
            'username': ' ',
            'email': ' ',
            'password': ' '
        }

    def test_user_signup_valid(self):
        response = self.client.post(
            self.urls['signup'],
            self.user_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['username'], self.user_data['username'])
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().username, self.user_data['username'])

        response = self.client.post(
            self.urls['login'],
            data={
                'login_identifier': self.user_data['email'],
                'password': self.user_data['password']
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_signup_weak_password_all_cases(self):
        data = self.user_data.copy()
        # lower letters only
        data['password'] = 'psw'
        response = self.client.post(
            self.urls['signup'],
            data=data,
            format='json'
        )
        errors = ' '.join(response.data['errors'])

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('8 characters long', errors)
        self.assertIn('uppercase letter', errors)
        self.assertIn('digit', errors)
        self.assertIn('special character', errors)

        # lower letters and 8 characters only
        data['password'] = 'password'
        response = self.client.post(
            self.urls['signup'],
            data=data,
            format='json',
            HTTP_X_API_VERSION='2.0'
        )

        errors = ' '.join(response.data['errors'])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('uppercase letter', errors)
        self.assertIn('digit', errors)
        self.assertIn('special character', errors)

        # lower and upper letters and 8 characters only
        data['password'] = 'Password'
        response = self.client.post(
            self.urls['signup'],
            data=data,
            format='json',
            HTTP_X_API_VERSION='2.0'
        )

        errors = ' '.join(response.data['errors'])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('digit', errors)
        self.assertIn('special character', errors)

        # missing special character
        data['password'] = 'Password1'
        response = self.client.post(
            self.urls['signup'],
            data=data,
            format='json'
        )

        errors = ' '.join(response.data['errors'])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('special character', errors)

        # all criteria
        data['password'] = 'Password1#'
        response = self.client.post(
            self.urls['signup'],
            data=data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_signup_with_no_data(self):
        response = self.client.post(
            self.urls['signup'],
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['username'][0].code, 'required')
        self.assertEqual(response.data['email'][0].code, 'required')
        self.assertEqual(User.objects.count(), 0)

    def test_user_signup_with_whitespace_data(self):
        response = self.client.post(
            self.urls['signup'],
            self.whitespace_user_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['username'][0].code, 'blank')
        self.assertEqual(response.data['email'][0].code, 'blank')
        self.assertEqual(User.objects.count(), 0)

    def test_user_signup_with_incomplete_data(self):
        data = self.user_data.copy()
        # remove email
        data.pop('email')

        response = self.client.post(
            self.urls['signup'],
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['email'][0].code, 'required')
        self.assertEqual(User.objects.count(), 0)

    def test_user_signup_slugify(self):
        response = self.client.post(
            self.urls['signup'],
            self.user_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().slug, slugify(self.user_data['username']))

    def test_user_signup_email_already_exists(self):
        data = self.user_data.copy()
        # change username
        data['username'] = 'test 1002'

        response = self.client.post(
            self.urls['signup'],
            self.user_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)

        response = self.client.post(
            self.urls['signup'],
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(response.data['email'][0].code, 'unique')

    def test_user_signup_username_already_exists(self):
        data = self.user_data.copy()
        # change email
        data['email'] = 'test.1002@gmail.com'

        response = self.client.post(
            self.urls['signup'],
            self.user_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)

        response = self.client.post(
            self.urls['signup'],
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(response.data['username'][0].code, 'unique')

    def test_user_signup_with_deleted_account(self):
        response = self.client.post(
            self.urls['signup'],
            self.user_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user = User.objects.get()
        user.deleted = True
        user.save()

        response = self.client.post(
            self.urls['signup'],
            self.user_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['username'], self.user_data['username'])
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().username, self.user_data['username'])

    def test_user_signup_profile_creation(self):
        response = self.client.post(
            self.urls['signup'],
            self.user_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Profile.objects.count(), 1)
        self.assertEqual(ProfilePrivacy.objects.count(), 1)

    def test_user_signup_event_publish(self):
        REDIS_URL = os.environ.get("REDIS_URL", None)
        redis_client = redis.from_url(
            REDIS_URL,
            decode_responses=True
        )

        events = []
        stop_listening = threading.Event()

        def listen_to_event():
            # subscribe and search for events
            with redis_client.pubsub() as pubsub:
                pubsub.subscribe(f'user_events')
                while True:
                    message = pubsub.get_message(ignore_subscribe_messages=True)
                    if message:
                        dump = json.loads(message['data'])
                        events.append(dump)
                    
                    if stop_listening.is_set():
                        break
        
        # start thread
        thread = threading.Thread(target=listen_to_event, daemon=True)
        thread.start()

        time.sleep(2)

        response = self.client.post(
            self.urls['signup'],
            self.user_data,
            format='json'
        )
        
        time.sleep(1)
        stop_listening.set()
        time.sleep(1)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertGreater(len(events), 0)
        self.assertEqual(events[0]['type'], 'create')
        self.assertEqual(events[0]['data']['username'], self.user_data['username'])
    
    
class TestPasswordResetView(TestSetup):
    def setUp(self):
        self.client.credentials(HTTP_X_API_VERSION='2.0')
        
        self.user = UserFactory.build()
        self.user.set_password('test123456')
        self.user.save()

        self.code = PasswordCodeFactory(
            user=self.user
        )

    def test_password_reset_valid(self):
        data = {
            'code': self.code.code,
            'password': 'Test123&'
        }
        response = self.client.post(
            self.urls['password-reset'],
            data=data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Password reset successful')

        # login with new password
        login_data = {
            'login_identifier': self.user.email,
            'password': 'Test123&'
        }

        response = self.client.post(
            self.urls['login'],
            data=login_data,
            format='json'
        )
    
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_password_reset_weak_password(self):
        # lower letters only
        data = {
            'code': self.code.code,
            'password': 'pwd'
        }
        response = self.client.post(
            self.urls['password-reset'],
            data=data,
            format='json'
        )
        
        errors = ' '.join(response.data['errors'])

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('8 characters long', errors)
        self.assertIn('uppercase letter', errors)
        self.assertIn('digit', errors)
        self.assertIn('special character', errors)

        # lower letters and 8 characters only
        data['password'] = 'password'
        response = self.client.post(
            self.urls['password-reset'],
            data=data,
            format='json',
            HTTP_X_API_VERSION='2.0'
        )

        errors = ' '.join(response.data['errors'])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('uppercase letter', errors)
        self.assertIn('digit', errors)
        self.assertIn('special character', errors)

        # lower and upper letters and 8 characters only
        data['password'] = 'Password'
        response = self.client.post(
            self.urls['password-reset'],
            data=data,
            format='json',
            HTTP_X_API_VERSION='2.0'
        )

        errors = ' '.join(response.data['errors'])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('digit', errors)
        self.assertIn('special character', errors)

        # missing special character
        data['password'] = 'Password1'
        response = self.client.post(
            self.urls['password-reset'],
            data=data,
            format='json'
        )

        errors = ' '.join(response.data['errors'])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('special character', errors)
        
        # all criteria
        data['password'] = 'Test123&'
        response = self.client.post(
            self.urls['password-reset'],
            data=data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # login with new password
        login_data = {
            'login_identifier': self.user.email,
            'password': 'Test123&'
        }

        response = self.client.post(
            self.urls['login'],
            data=login_data,
            format='json'
        )
    
        self.assertEqual(response.status_code, status.HTTP_200_OK)
  
    def test_password_reset_resubmit_code(self):
        data = {
            'code': self.code.code,
            'password': 'Test123@'
        }
        response = self.client.post(
            self.urls['password-reset'],
            data=data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # re-submit
        response = self.client.post(
            self.urls['password-reset'],
            data=data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Failed to verify code', response.data['message'])

    def test_password_reset_deleted_account(self):
        # create deleted user
        deleted_user = UserFactory.build()
        deleted_user.deleted = True
        deleted_user.save()
        
        deleted_user_code = PasswordCodeFactory(
            user=deleted_user
        )
        
        data = {
            'code': deleted_user_code.code,
            'password': 'test123'
        }
        response = self.client.post(
            self.urls['password-reset'],
            data=data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['message'], 'User not found')
    
    def test_password_reset_no_code_existing(self):
        self.code.delete()
        data = {
            'code': self.code.code,
            'password': 'Test123@'
        }
        response = self.client.post(
            self.urls['password-reset'],
            data=data,
            format='json'
        )
        
        # doesn't show that code is not found
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Failed to verify code', response.data['message'])

    def test_password_reset_multiple_code_exist(self):
        # created a duplicate code
        code2 = PasswordCodeFactory.build(
            user=self.user
        )
        code2.code = self.code.code
        code2.save()

        data = {
            'code': self.code.code,
            'password': 'test123'
        }

        response = self.client.post(
            self.urls['password-reset'],
            data=data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('System error', response.data['message'])

        ## ensure requesting a new code fixes the issue
        # issuing a new code
        data = {
            'email': self.user.email
        }
        response = self.client.post(
            self.urls['password-forgot'],
            data=data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # find the new code
        from apps.users.models import PasswordResetCode
        new_code = PasswordResetCode.objects.filter(user=self.user).first().code
        
        data = {
            'code': new_code,
            'password': 'Test123$'
        }

        response = self.client.post(
            self.urls['password-reset'],
            data=data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

  
    