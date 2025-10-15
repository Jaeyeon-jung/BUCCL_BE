from datetime import datetime
import logging
from django.test import TestCase
from .models import AuthSMS

logger = logging.getLogger('django')

class SMSUnitTest(TestCase):
    def setUp(self):
        self.p_number = "01012345678"
        self.auth_sms = AuthSMS.objects.create(hp=self.p_number, auth=None, created=datetime.now(), modified=datetime.now())
        self.a_number = self.auth_sms.auth
        self.wrong_a_number = "567890"

    def test_check_auth_number(self):
        logger.debug("auth_sms : %s", self.auth_sms.__dict__)
        self.assertEqual(self.auth_sms.hp, self.p_number)
        self.assertTrue(AuthSMS.check_auth_number(self.p_number, self.a_number))
        self.assertFalse(AuthSMS.check_auth_number(self.p_number, self.wrong_a_number))

