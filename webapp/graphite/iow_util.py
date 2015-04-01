from django.conf import settings

def get_tenant(request):
  tenant = ""
  if 'tenant' in request.GET:
    tenant = request.GET['tenant']
  elif 'tenant' in request.session:
    tenant = request.session['tenant']
  else:
    tenant = None
  return check_tenant(tenant)

def check_tenant(tenant):
  if tenant not in settings.TENANT_LIST:
    return settings.TENANT_LIST[0]
  return tenant
