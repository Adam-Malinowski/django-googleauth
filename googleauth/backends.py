import logging
import time

from django.conf import settings
from django.db.models import get_model
from django.contrib.auth.models import User, Group

IS_STAFF = getattr(settings, 'GOOGLEAUTH_IS_STAFF', False)
GROUPS = getattr(settings, 'GOOGLEAUTH_GROUPS', tuple())
APPS_DOMAIN = getattr(settings, 'GOOGLEAUTH_APPS_DOMAIN', None)
CLEAN_USERNAME = getattr(settings, 'GOOGLEAUTH_APPS_CLEAN_USERNAME', False)
USERPROFILE_MODEL = getattr(settings, 'GOOGLEAUTH_USERPROFILE_MODEL', None)
PROFILE_FIELDS = getattr(settings, 'GOOGLEAUTH_PROFILE_FIELDS', None)

logger = logging.getLogger(__name__)


class GoogleAuthBackend(object):

    def authenticate(self, identifier=None, attributes=None):
        start = time.time()
        email = attributes.get('email', None)
        (username, domain) = email.split('@')

        if CLEAN_USERNAME:
            username = filter(str.isalpha, str(username).lower())

        if APPS_DOMAIN and APPS_DOMAIN != domain:
            return None

        try:

            try:

                user = User.objects.get(email=email)

            except User.MultipleObjectsReturned:

                user = User.objects.get(username=username, email=email)

        except User.DoesNotExist:

            user = User.objects.create(username=username, email=email)
            user.first_name = attributes.get('first_name') or ''
            user.last_name = attributes.get('last_name') or ''
            user.is_staff = IS_STAFF
            user.set_unusable_password()

            for group in GROUPS:
                try:
                    grp = Group.objects.get(name=group)
                    user.groups.add(grp)
                except:
                    pass

            user.save()

        if USERPROFILE_MODEL and PROFILE_FIELDS:
            model_details = USERPROFILE_MODEL.rsplit('.', 1)

            model = get_model(model_details[0], model_details[1])
            try:
                model.objects.get(user=user)
            except model.DoesNotExist:
                self.save_user_profile(model, user, attributes)
        print 'backend auth in %s' % (time.time() - start)
        logger.critical('backend auth in %s' % (time.time() - start))
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            pass

    def save_user_profile(self, model, user, attributes):
        start = time.time()
        to_save = {'user': user}
        for google_field, profile_field in PROFILE_FIELDS.iteritems():
            to_save[profile_field] = attributes.get(google_field, None)

        userprofile = model(**to_save)
        userprofile.save()
        logger.info('backend save in %s' % (time.time() - start)) 
