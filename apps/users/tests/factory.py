import factory
from apps.users.models import User, PasswordResetCode
import random

class UserFactory(factory.django.DjangoModelFactory):
    class Meta: 
        model = User
    
    username = factory.Faker('name')
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'default_password')


class PasswordCodeFactory(factory.django.DjangoModelFactory):
    class Meta: 
        model = PasswordResetCode

    user = factory.SubFactory(UserFactory)
    code = factory.Sequence(lambda _: str(random.randint(100000, 999999)))