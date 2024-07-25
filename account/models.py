from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser

class UserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, address, phone, age, password=None):
        if not email:
            raise ValueError('User must have an email address')
        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            address=address,
            phone=phone,
            age=age,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, address, phone, age, password=None):
        user = self.create_user(
            email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            address=address,
            phone=phone,
            age=age,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):
    email = models.EmailField(
        verbose_name='Email',
        max_length=255,
        unique=True,
    )
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    age = models.PositiveIntegerField()
    no_of_files_uploaded = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'address', 'phone', 'age']

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin

class File(models.Model):
    file = models.FileField(upload_to='uploads/')
    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
