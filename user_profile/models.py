import json
from django.contrib.auth.models import AbstractUser

from django.db import models
import requests


class Team(models.Model):
    slack_id = models.CharField(max_length=10, default='')

    next_crawl_member_time = models.DateTimeField(auto_now_add=True)

    created_by_slack_id = models.CharField(max_length=10, default='')


    def get_creator(self):
        return User.objects.get(slack_id=self.created_by_slack_id)

    def parse_members(self):
        url = 'https://slack.com/api/users.list?token=' + self.get_creator().slack_access_token
        r = requests.get(url)

        try:

            members = json.loads(r.content)['members']
            for m in members:
                if m['profile'].get('email'):
                    user, created = User.objects.get_or_create(slack_id=m['id'], email=m['profile']['email'],
                                                       username=m['profile']['email'][:30])
                else:
                    user, created = User.objects.get_or_create(slack_id=m['id'], email=m['id'],
                                                               username=m['id'])

                user.slack_team_id = self.slack_id
                user.slack_username =  m['name']
                user.slack_avatar =  m['profile'].get('image_24','')

                user.save()
            return User.objects.filter(slack_team_id = self.slack_id)
        except Exception, exc:
            print exc
            import ipdb; ipdb.set_trace()

# Create your models here.
class User(AbstractUser):
    slack_id = models.CharField(max_length=10, default='')
    slack_username = models.CharField(max_length=100, default='')
    slack_avatar = models.CharField(max_length=500, default='')
    slack_team_id = models.CharField(max_length=10, default='')
    slack_access_token = models.CharField(max_length=120, default='')

    team = models.ForeignKey(Team, null=True)

    def get_team(self):
        if self.team is None:
            team, created = Team.objects.get_or_create(slack_id=self.slack_team_id)
            team.created_by_slack_id = self.slack_id
            team.save()
            self.team = team
            self.save()

        return self.team








