from django.db import models
from django.db.models.signals import pre_save


class BulkManager(models.Manager):

    def bulk_create(self, objs, **kwargs):
        bulk_create = super(models.Manager, self).bulk_create(objs, **kwargs)
        for obj in objs:
            pre_save.send(obj.__class__, instance=obj)
        return bulk_create
    
    def bulk_update(self, objs, **kwargs):
        bulk_update = super(models.Manager, self).bulk_update(objs, **kwargs)
        for obj in objs:
            pre_save.send(obj.__class__, instance=obj)
        return bulk_update