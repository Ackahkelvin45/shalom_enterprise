from django.db import models

# Create your models here.


class Settings(models.Model):
    customer_support_number=models.CharField(max_length=20,null=True,blank=True)
    company_email=models.EmailField(null=True,blank=True)
    company_address=models.TextField(null=True,blank=True)
    about_us=models.TextField(null=True,blank=True)
    privacy_policy=models.TextField(null=True,blank=True)
    terms_and_conditions=models.TextField(null=True,blank=True)
    shipping_policy=models.TextField(null=True,blank=True)
    return_policy=models.TextField(null=True,blank=True)
    cancellation_policy=models.TextField(null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.customer_support_number
    


class SocialMedia(models.Model):
    facebook=models.URLField(null=True,blank=True)
    twitter=models.URLField(null=True,blank=True)
    instagram=models.URLField(null=True,blank=True)
    linkedin=models.URLField(null=True,blank=True)
    youtube=models.URLField(null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.facebook
    

