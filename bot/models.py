from django.db import models

class FakeName(models.Model):
    name = models.CharField(max_length=300, primary_key = True)

    def __str__(self):
        return self.name
