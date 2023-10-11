from builtins import object
from app2.models import NiceModel

class ProxyModel(NiceModel):
    class Meta(object):
        proxy = True
