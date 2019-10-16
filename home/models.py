from django.db import models


class TestModel(models.Model):
    test_name = models.CharField(max_length=100)
    test_data = models.CharField(max_length=200)

    def __str__(self):
        return self.test_name


class FirstRun(models.Model):
    myshopify_domain = models.CharField(max_length=100, help_text='Shopify store domain.', unique=True)
    status = models.BooleanField(default=True, help_text='True if its the first visit, else False')

    def __str__(self):
        return self.status
