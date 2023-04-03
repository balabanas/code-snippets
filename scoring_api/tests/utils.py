import datetime
import hashlib

from scoring_api import api


def set_valid_auth(request):
    """Sets valid authorization token to be passed with test requests to the API"""
    if request.get("login") == api.ADMIN_LOGIN:
        msg = datetime.datetime.now().strftime("%Y%m%d%H") + api.ADMIN_SALT
        request["token"] = hashlib.sha512(msg.encode()).hexdigest()
    else:
        msg = request.get("account", "") + request.get("login", "") + api.SALT
        request["token"] = hashlib.sha512(msg.encode()).hexdigest()
