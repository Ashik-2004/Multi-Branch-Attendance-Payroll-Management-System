from django.db import models

# Create your models here.
class tbl_login(models.Model):
    email=models.EmailField(max_length=100)
    password=models.CharField(max_length=25)
    user_role=models.CharField(max_length=25)
    def __str__(self):
        return self.email
