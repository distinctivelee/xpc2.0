
from django.db import models
from web.models.composer import Composer
from web.models.copyright import Copyright

class Post(models.Model):
    pid = models.BigIntegerField(primary_key=True)
    title = models.CharField(max_length=256)
    thumbnail = models.CharField(max_length=512, blank=True, null=True)
    preview = models.CharField(max_length=512, blank=True, null=True)
    video = models.CharField(max_length=512, blank=True, null=True)
    video_format = models.CharField(max_length=32, blank=True, null=True)
    category = models.CharField(max_length=512)
    created_at = models.CharField(max_length=128)
    description = models.TextField(blank=True, null=True)
    play_counts = models.IntegerField()
    like_counts = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'posts'

    @property
    def composers(self):
        # 取出当前作品的所有作者

        composers = []
        cr_list = Copyright.objects.filter(pid=self.pid).all()
        for cr in cr_list:
            composer = Composer.objects.get(cid = cr.cid)
            composer.role = cr.roles
            composers.append(composer)
        return composers