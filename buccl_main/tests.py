from django.test import TestCase, RequestFactory
from django.urls import reverse
from unittest.mock import patch, MagicMock
import json
import jwt
from datetime import datetime

from .views import PaymentResult, PrePaymentCheckView
from .models import Order, Payment, PaymentDetail, PaymentCancel, Product, ProductType, Sport
from buccl_user.models import User
