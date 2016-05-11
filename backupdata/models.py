from datetime import datetime, timedelta
import json
from django.db import models

# Create your models here.
import re
import requests
from user_profile.models import User


def crawl_all_channel(user):
    try:
        url = "https://slack.com/api/channels.list?token=" + user.slack_access_token
        resp = requests.get(url)
        channels = parse_channel(user, json.loads(resp.content)['channels'], False, False)

        url = "https://slack.com/api/groups.list?token=" + user.slack_access_token
        resp = requests.get(url)
        groups = parse_channel(user, json.loads(resp.content)['groups'], True, False)

        url = "https://slack.com/api/im.list?token=" + user.slack_access_token
        resp = requests.get(url)
        im = parse_channel(user, json.loads(resp.content)['ims'], False, True)

        return channels, groups, im

    except Exception, exc:
        import ipdb; ipdb.set_trace();


    return [], [], []


def parse_channel(user, json_channels, is_privategroup, is_im=False):
    channels = []

    for c in json_channels:
        channel, created = Channel.objects.get_or_create(slack_id=c['id'])
        channel.name = c.get('name', c.get('user', c['id']))
        try:
            channel.topic = c['topic']['value']
        except:
            pass

        try:
            channel.purpose = c['purpose']['value']
        except:
            pass
        channel.is_archived = c.get('is_archived', False)
        channel.is_privategroup = is_privategroup
        channel.is_im = is_im
        channel.save()
        channels.append(channel)

        if is_privategroup:
            members = c.get('members',[])
            for m in members:
                if m == user.slack_id:
                    ChannelMember.objects.get_or_create(channel=channel, user=user)
        elif c.get('is_member', ''):
            ChannelMember.objects.get_or_create(channel=channel, user=user)

    return channels


def add_messages(messages, channel):
    for m in messages:
        ts = datetime.fromtimestamp(float(m.get('ts', 0)))

        user_slack_id = m.get('user', '')
        message_type = m.get('type', '')
        if user_slack_id != '' and message_type != '' and ts != None:
            message, created = Message.objects.get_or_create(user_slack_id=user_slack_id, message_type= message_type, ts=ts,
                                                             channel=channel)
            message.text = m.get('text', '')
            message.save()


class Channel(models.Model):
    name = models.CharField(max_length=100, default='')
    topic = models.TextField(default='')
    purpose = models.TextField(default='')
    slack_id = models.CharField(max_length=10, default='')
    creator_slack_id = models.CharField(max_length=10, default='')

    next_crawl_time = models.DateTimeField(auto_now_add=True)
    next_crawl_cycle = models.IntegerField(default=1)  # hours

    is_privategroup = models.BooleanField(default=False)
    is_im = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)

    latest_crawled = models.DateTimeField(null=True)
    oldest_crawled = models.DateTimeField(null=True)

    def __unicode__(self):
        return self.name

    def get_creator(self):
        u = None
        print "self.name: " + self.name
        #print "self.creator_slack_id: " + self.creator_slack_id
        if self.creator_slack_id:
            u = User.objects.get(slack_id=self.creator_slack_id)
        else:
            u = ChannelMember.objects.filter(channel=self)
            if u.count() > 0:
                u = u[0].user
            else:
                u = None
        return u or User.objects.get(username='issac@issackelly.com')

    def crawl_history(self):

        if self.get_creator() is None:
            return

        if self.is_privategroup:
            url = 'https://slack.com/api/groups.history'
        elif self.is_im:
            url = 'https://slack.com/api/im.history'
        else:
            url = 'https://slack.com/api/channels.history'

        url += "?token=" + self.get_creator().slack_access_token

        epoch = datetime.fromtimestamp(0)

        if self.oldest_crawled is None:
            self.oldest_crawled = datetime.now()
            self.latest_crawled = datetime.now()
            self.save()

        while self.oldest_crawled > epoch:
            url += "&channel=" + self.slack_id
            url += "&latest=" + str((self.oldest_crawled - datetime(1970, 1, 1)).total_seconds())

            try:
                resp = requests.get(url)
                js = json.loads(resp.content)

                messages = js['messages']
            except Exception, exc:
                import ipdb; ipdb.set_trace()

            if len(messages) > 0:
                latest =  messages[-1]['ts']
                has_more = js['has_more']
                if has_more:
                    self.oldest_crawled = datetime.fromtimestamp(float(latest))
                else:
                    self.oldest_crawled = datetime.fromtimestamp(0)

                add_messages(messages, self)


            else:
                self.oldest_crawled = datetime.fromtimestamp(0)
            self.save()

        now = datetime.now()

        while self.latest_crawled < now:
            url += "&channel=" + self.slack_id
            url += "&oldest=" + str((self.latest_crawled - datetime(1970, 1, 1)).total_seconds())

            self.latest_crawled = self.latest_crawled + timedelta(hours=12)
            if self.latest_crawled > now:
                self.latest_crawled = now
            self.save()

            url += "&latest=" + str((self.latest_crawled - datetime(1970, 1, 1)).total_seconds())

            r = requests.get(url)
            js = json.loads(r.content)
            messages = js['messages']

            if len(messages) == 0:
                 self.latest_crawled = now
            else:
                add_messages(messages, self)




            self.save()

        self.next_crawl_time += timedelta(hours=self.next_crawl_cycle)
        self.save()


class ChannelMember(models.Model):
    channel = models.ForeignKey(Channel)
    user = models.ForeignKey(User)

    def __unicode__(self):
        name = ''
        if self.channel and self.channel.name:
            name += self.channel.name + " "
        if self.user and self.user.slack_username:
            name += self.user.slack_username

        return name


class Message(models.Model):
    message_type = models.CharField(max_length=50, default='', db_index=True)
    message_subtype = models.CharField(max_length=50, default='', db_index=True)
    hidden = models.BooleanField(default=False)
    ts = models.DateTimeField(null=True, db_index=True)
    deleted_ts = models.DateTimeField(null=True)
    event_ts = models.DateTimeField(null=True)

    user_slack_id = models.CharField(max_length=10, default='', db_index=True)
    user = models.ForeignKey(User, null=True)
    text = models.TextField(default='')

    channel = models.ForeignKey(Channel, null=True)

    def get_user(self):
        if self.user is None:
            u = User.objects.filter(slack_id=self.user_slack_id)[0]
            self.user = u
            self.save()

        return self.user

    def get_text(self):
        p = re.compile('<(.*?)>')
        results = p.findall(self.text)
        for m in results:
            if m.startswith('@U'):
                slack_id = m.replace("@",'').split("|")[0]
                try:
                    user = User.objects.get(slack_id = slack_id)
                except:
                    user = None

                if user:
                    self.text = self.text.replace("<" + m + ">", user.slack_username )

            if m.startswith('http'):
                link = m.split("|")[0]
                self.text = self.text.replace("<" + m + ">", "<a href='"+link + "'>" + link + "</a>" )


        return self.text
