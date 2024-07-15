# # from django.db import models

# # class APICall(models.Model):
# #     prompt = models.TextField()
# #     lang = models.CharField(max_length=20, blank=True, null=True)
# #     image = models.ImageField(upload_to='uploads/', blank=True, null=True)
# #     ip_address = models.GenericIPAddressField()
# #     response_data = models.JSONField()
# #     created_at = models.DateTimeField(auto_now_add=True)

# #     def __str__(self):
# #         return f"API Call {self.id} - {self.prompt[:50]}"


# from django.db import models

# class APICall(models.Model):
#     prompt = models.TextField(blank=True, null=True)
#     lang = models.CharField(max_length=20, blank=True, null=True)
#     image = models.ImageField(upload_to='uploads/', blank=True, null=True)
#     document = models.FileField(upload_to='documents/', blank=True, null=True)
#     ip_address = models.GenericIPAddressField()
#     response_data = models.JSONField()
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"API Call {self.id} - {self.prompt[:50]}"



from django.db import models

class APICall(models.Model):
    prompt = models.TextField(blank=True, null=True)  # Consider storing the prompt or context
    lang = models.CharField(max_length=20, blank=True, null=True)  # Example: programming language
    image = models.ImageField(upload_to='uploads/', blank=True, null=True)  # Optional: for image uploads
    document = models.FileField(upload_to='documents/', blank=True, null=True)  # Optional: for document uploads
    code = models.TextField(blank=True, null=True)  # Field to store the code snippet
    ip_address = models.GenericIPAddressField()
    response_data = models.JSONField()  # Store API response data as JSON
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"API Call {self.id} - {self.prompt[:50]}"
