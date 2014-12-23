from django.conf import settings

def check_tenant(tenant):
    if tenant not in settings.TENANT_LIST:
        return settings.TENANT_LIST[0]
    return tenant
