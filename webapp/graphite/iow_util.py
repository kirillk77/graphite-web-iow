from django.conf import settings

def get_tenant(request):
  tenant = ""
  if 'tenant' in request.GET:
    tenant = request.GET['tenant']
  else:
    tenant = request.session['tenant']
  return check_tenant(tenant)

def check_tenant(tenant):
  if tenant not in settings.TENANT_LIST:
    return settings.TENANT_LIST[0]
  return tenant
