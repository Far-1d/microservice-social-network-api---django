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

load_dotenv()

class TestSignupView(TestSetup):
    def t1est_user_signup_valid(self):
        response = self.client.post(
            self.urls['signup'],
            self.user_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['username'], self.user_data['username'])
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().username, self.user_data['username'])

    def t1est_user_signup_with_no_data(self):
        response = self.client.post(
            self.urls['signup'],
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['username'][0].code, 'required')
        self.assertEqual(response.data['email'][0].code, 'required')
        self.assertEqual(User.objects.count(), 0)
    
    def t1est_user_signup_with_whitespace_data(self):
        response = self.client.post(
            self.urls['signup'],
            self.whitespace_user_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['username'][0].code, 'blank')
        self.assertEqual(response.data['email'][0].code, 'blank')
        self.assertEqual(User.objects.count(), 0)

    def t1est_user_signup_with_incomplete_data(self):
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
    
    def t1est_user_signup_slugify(self):
        response = self.client.post(
            self.urls['signup'],
            self.user_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().slug, slugify(self.user_data['username']))

    def t1est_user_signup_email_already_exists(self):
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
    
    def t1est_user_signup_username_already_exists(self):
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

    def t1est_user_signup_with_deleted_account(self):
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

    def t1est_user_signup_profile_creation(self):
        response = self.client.post(
            self.urls['signup'],
            self.user_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Profile.objects.count(), 1)
        self.assertEqual(ProfilePrivacy.objects.count(), 1)

    def t1est_user_signup_event_publish(self):
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
    

class TestLoginView(TestSetup):
    def setUp(self):
        self.user = UserFactory.build()
        self.user.set_password('test123456')
        self.user.save()

        self.deleted_user = UserFactory.build()
        self.deleted_user.set_password('test123456')
        self.deleted_user.deleted = True
        self.deleted_user.deleted_at = timezone.now()
        self.deleted_user.save()

    def t1est_user_login_with_email_valid(self):
        data = {
            'login_identifier': self.user.email,
            'password': 'test123456'
        }

        response = self.client.post(
            self.urls['login'],
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['username'], self.user.username)
    
    def t1est_user_login_with_username_valid(self):
        data = {
            'login_identifier': self.user.username,
            'password': 'test123456'
        }

        response = self.client.post(
            self.urls['login'],
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['username'], self.user.username)

    def t1est_user_login_wrong_password(self):
        data = {
            'login_identifier': self.user.email,
            'password': 'wrong_passsword'
        }

        response = self.client.post(
            self.urls['login'],
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'Unable to log in with provided credentials')
    
    def t1est_user_login_incomplete_body(self):
        data_no_password = {
            'login_identifier': self.user.email,
        }
        data_no_identifier = {
            'password': 'test123456',
        }

        response = self.client.post(
            self.urls['login'],
            data_no_password,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['password'][0].code, 'required')

        response = self.client.post(
            self.urls['login'],
            data_no_identifier,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['login_identifier'][0].code, 'required')

    def t1est_user_login_no_body(self):
        response = self.client.post(
            self.urls['login'],
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['password'][0].code, 'required')
        self.assertEqual(response.data['login_identifier'][0].code, 'required')

    def t1est_user_login_returns_tokens_and_user_data(self):
        data = {
            'login_identifier': self.user.email,
            'password': 'test123456'
        }

        response = self.client.post(
            self.urls['login'],
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertListEqual(list(response.data.keys()), ['refresh', 'access', 'user'])

    def t1est_user_login_whitespace_data(self):
        data = {
            'login_identifier': '  ',
            'password': '  '
        }

        response = self.client.post(
            self.urls['login'],
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def t1est_user_login_deleted_user(self):
        data = {
            'login_identifier': self.deleted_user.email,
            'password': 'test123456'
        }

        response = self.client.post(
            self.urls['login'],
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def t1est_user_login_case_sensetive_password(self):
        data = {
            'login_identifier': self.user.email,
            'password': 'TEST123456'
        }

        response = self.client.post(
            self.urls['login'],
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['message'], 'User not found')

    def t1est_user_login_case_sensetive_email(self):
        data = {
            'login_identifier': str(self.user.email).upper(),
            'password': 'test123456'
        }

        response = self.client.post(
            self.urls['login'],
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def t1est_user_login_case_sensetive_username(self):
        data = {
            'login_identifier': str(self.user.username).upper(),
            'password': 'test123456'
        }

        response = self.client.post(
            self.urls['login'],
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def t1est_user_login_invalid_methods(self):
        data = {
            'login_identifier': self.user.username,
            'password': 'test123456'
        }

        response_get = self.client.get(
            self.urls['login'],
            data,
            format='json'
        )

        response_put = self.client.put(
            self.urls['login'],
            data,
            format='json'
        )
        response_patch = self.client.patch(
            self.urls['login'],
            data,
            format='json'
        )
        response_delete = self.client.delete(
            self.urls['login'],
            data,
            format='json'
        )

        self.assertEqual(response_get.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response_put.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response_patch.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response_delete.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def t1est_user_login_already_logged_in(self):
        self.client.force_authenticate(user=self.user) 

        data = {
            'login_identifier': self.user.email,
            'password': 'test123456'
        }

        response = self.client.post(
            self.urls['login'],
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'You are already logged in')


class TestGetUserView(TestSetup):
    def setUp(self):
        self.user = UserFactory.build()
        self.client.force_authenticate(user=self.user) 

    def tearDown(self):
        self.client.force_authenticate(user=None) 

    def t1est_get_user_valid(self):
        response = self.client.get(
            self.urls['read']
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user.username)
    
    def t1est_get_user_not_authenticated(self):
        self.client.force_authenticate(user=None) 

        response = self.client.get(
            self.urls['read']
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def t1est_get_user_invalid_method(self):
        response_post = self.client.post(
            self.urls['read']
        )
        response_put = self.client.put(
            self.urls['read']
        )
        response_patch = self.client.patch(
            self.urls['read']
        )
        response_delete = self.client.delete(
            self.urls['read']
        )
        response_options = self.client.options(
            self.urls['read']
        )

        self.assertEqual(response_post.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response_put.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response_patch.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response_delete.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response_options.status_code, status.HTTP_200_OK)


class TestForgotPasswordView(TestSetup):
    def setUp(self):
        self.user = UserFactory.build()

    def t1est_forgot_password_valid(self):
        data = {
            'email': self.user.email
        }

        response = self.client.post(
            self.urls['password-forgot'],
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'If this email exists, a reset code has been sent')

    def t1est_forgot_password_not_existing_email(self):
        data = {
            'email': 'unknown@gmail.com'
        }

        response = self.client.post(
            self.urls['password-forgot'],
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'If this email exists, a reset code has been sent')

    def t1est_forgot_password_bad_format_email(self):
        data = {
            'email': 'unknown.gmail'
        }

        response = self.client.post(
            self.urls['password-forgot'],
            data,
            format='json'
        )
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['email'][0].code, 'invalid')

    def t1est_forgot_password_already_logged_in(self):
        self.client.force_authenticate(self.user)
        
        data = {
            'email': self.user.email
        }

        response = self.client.post(
            self.urls['password-forgot'],
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'If this email exists, a reset code has been sent')

    def t1est_forgot_password_resubmit_request(self):
        data = {
            'email': self.user.email
        }

        response = self.client.post(
            self.urls['password-forgot'],
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            self.urls['password-forgot'],
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestPasswordResetView(TestSetup):
    def setUp(self):
        self.user = UserFactory.build()
        self.user.set_password('test123456')
        self.user.save()

        self.code = PasswordCodeFactory(
            user=self.user
        )

        self.client.force_authenticate(user=None)

    def test_password_reset_valid(self):
        data = {
            'code': self.code.code,
            'password': 'test123'
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
            'password': 'test123'
        }

        response = self.client.post(
            self.urls['login'],
            data=login_data,
            format='json'
        )
    
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        

    def t1est_password_reset_resubmit_code(self):
        pass
    
    def t1est_password_reset_deleted_account(self):
        pass
    
    def t1est_password_reset_resubmit_code(self):
        pass
    
    def t1est_password_reset_no_code_existing(self):
        pass

    def t1est_password_reset_multiple_code_exist(self):
        pass

class TestUpdateUserView(TestSetup):
    def setUp(self):
        self.user = UserFactory.build()
        self.user.set_password('test123456')
        self.user.save()
        
        self.deleted_user = UserFactory.build()
        self.deleted_user.set_password('test123456')
        self.deleted_user.deleted = True
        self.deleted_user.deleted_at = timezone.now()
        self.deleted_user.save()

        self.client.force_authenticate(user=self.user)

    def t1est_user_update_valid(self):
        data = {
            'email': 'new_email@gmail.com',
            'password': 'test123'
        }

        response = self.client.patch(
            self.urls['update'],
            data=data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], data['email'])
        self.assertEqual(User.objects.filter(email=data['email']).count(), 1)
    
    def t1est_user_update_whitespace_body(self):
        data_white_email = {
            'email': '  ',
            'password': 'test123'
        }
        data_white_password = {
            'email': 'new_email@gmail.com',
            'password': '  '
        }

        response_white_email = self.client.patch(
            self.urls['update'],
            data=data_white_email,
            format='json'
        )

        response_white_password = self.client.patch(
            self.urls['update'],
            data=data_white_password,
            format='json'
        )

        self.assertEqual(response_white_email.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_white_email.data['email'][0].code, 'blank')
        self.assertEqual(response_white_password.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_white_password.data['password'][0].code, 'blank')
    
    def t1est_user_update_bad_format_fields(self):
        data = {
            'email': 'new_email.gmail',
            'password': 'test123'
        }

        response = self.client.patch(
            self.urls['update'],
            data=data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['email'][0].code, 'invalid')
    
    def t1est_user_update_incomplete_body(self):
        data_no_email = {
            'password': 'test123'
        }
        data_no_password = {
            'email': 'new_email@gmail.com',
        }

        response_no_email = self.client.patch(
            self.urls['update'],
            data=data_no_email,
            format='json'
        )

        response_no_password = self.client.patch(
            self.urls['update'],
            data=data_no_password,
            format='json'
        )

        # it is patch, so any bit of data can be updated
        self.assertEqual(response_no_email.status_code, status.HTTP_200_OK)
        self.assertEqual(response_no_password.status_code, status.HTTP_200_OK)
    
    def t1est_user_update_not_updatable_fields(self):
        data = {
            'username': 'new username',
            'slug': 'new_cool_username',
            'is_active': True,
            'is_staff': True
        }

        response = self.client.patch(
            self.urls['update'],
            data=data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'Only email and password are updatable')

    def t1est_user_update_deleted_user(self):
        self.client.force_authenticate(user=self.deleted_user)
        data = {
            'email': 'new_email@gmail.com',
            'password': 'test123'
        }

        response = self.client.patch(
            self.urls['update'],
            data=data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def t1est_user_update_not_authenticated(self):
        self.client.force_authenticate(user=None)
        data = {
            'email': 'new_email@gmail.com',
            'password': 'test123'
        }

        response = self.client.patch(
            self.urls['update'],
            data=data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def t1est_user_update_event_published(self):
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

        data = {
            'email': 'new_cool_email@gmail.com',
        }

        response = self.client.patch(
            self.urls['update'],
            data,
            format='json'
        )
        
        time.sleep(1)
        stop_listening.set()
        time.sleep(1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(events), 0)
        self.assertEqual(events[0]['type'], 'update')
        self.assertEqual(events[0]['data']['email'], data['email'])
    
    def t1est_user_update_invalid_methods(self):
        data = {
            'email': 'new_email@gmail.com',
            'password': 'test123'
        }

        response_put = self.client.put(
            self.urls['update'],
            data=data,
            format='json'
        )

        response_post = self.client.post(
            self.urls['update'],
            data=data,
            format='json'
        )
        response_get = self.client.get(
            self.urls['update'],
            format='json'
        )
        response_delete = self.client.delete(
            self.urls['update'],
            data=data,
            format='json'
        )

        self.assertEqual(response_put.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response_post.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response_get.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response_delete.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class TestDeleteUserView(TestSetup):
    def setUp(self):
        self.user = UserFactory.build()
        self.client.force_authenticate(user=self.user)

    def t1est_user_delete_valid(self):
        response = self.client.delete(
            self.urls['delete']
        )
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def t1est_user_delete_already_deleted(self):
        self.client.delete(
            self.urls['delete']
        )
        # delete again
        response = self.client.delete(
            self.urls['delete']
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def t1est_user_delete_event_published(self):
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

        response = self.client.delete(
            self.urls['delete']
        )
        
        time.sleep(1)
        stop_listening.set()
        time.sleep(1)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertGreater(len(events), 0)
        self.assertEqual(events[0]['type'], 'delete')
        self.assertEqual(events[0]['data']['email'], self.user.email)

    def t1est_user_delete_not_authenticated(self):
        self.client.force_authenticate(user=None)

        response = self.client.delete(
            self.urls['delete']
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    
    