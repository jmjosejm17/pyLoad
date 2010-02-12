# Create your views here.
from os.path import join

from django.conf import settings
from django.core.serializers import json
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseServerError
from django.utils import simplejson
  
def permission(perm):
    def _dec(view_func):
        def _view(request, * args, ** kwargs):
            if request.user.has_perm(perm) and request.user.is_authenticated():
                return view_func(request, * args, ** kwargs)
            else:
                return HttpResponseForbidden()
        
        _view.__name__ = view_func.__name__
        _view.__dict__ = view_func.__dict__
        _view.__doc__ = view_func.__doc__

        return _view

    return _dec

class JsonResponse(HttpResponse):
    def __init__(self, object):
        content = simplejson.dumps(
                                   object, indent=2, cls=json.DjangoJSONEncoder,
                                   ensure_ascii=False)
        super(JsonResponse, self).__init__(
                                           content)#, content_type='application/json') #@TODO uncomment
        self['Cache-Control'] = 'no-cache, must-revalidate'


@permission('pyload.can_add')
def add_package(request):
    
    name = request.POST['add_name']

    queue = int(request.POST['add_dest'])

    links = request.POST['add_links'].replace(" ","\n").split("\n")
    
    try:
        f = request.FILES['add_file']
        
        if name == None or name == "":
            name = f.name
            
        fpath = join(settings.DL_ROOT, f.name)
        destination = open(fpath, 'wb')
        for chunk in f.chunks():
            destination.write(chunk)
        destination.close()
        links.insert(0, fpath)
    except:
        pass
    
    if name == None or name == "":
        return HttpResponseServerError()
    
    links = filter(lambda x: x != "", links)
    
    settings.PYLOAD.add_package(name, links, queue)
        
    return JsonResponse("success")

@permission('pyload.can_add_dl')
def remove_link(request, id):
    try:
        settings.PYLOAD.del_links([int(id)])
        return JsonResponse("sucess")
    except:
        return HttpResponseServerError()

@permission('pyload.can_see_dl')    
def status(request):
    try:
        return JsonResponse(settings.PYLOAD.status_server())
    except:
        return HttpResponseServerError()

@permission('pyload.can_see_dl')
def links(request):
    try:
        links = settings.PYLOAD.status_downloads()
        ids = map(lambda x: x['id'], links)
        data = {}
        data['links'] = links
        data['ids'] = ids
        return JsonResponse(data)
    except:
        return HttpResponseServerError()

@permission('pyload.can_see_dl')
def queue(request):
    try:
        return JsonResponse(settings.PYLOAD.get_queue())
        
    except:
        return HttpResponseServerError()
        
        
@permission('pyload.can_change_satus')
def pause(request):
    try:
        return JsonResponse(settings.PYLOAD.pause_server())
        
    except:
        return HttpResponseServerError()


@permission('pyload.can_change_status')
def unpause(request):
    try:
        return JsonResponse(settings.PYLOAD.unpause_server())
        
    except:
        return HttpResponseServerError()
        

@permission('pyload.can_change_status')
def cancel(request):
    try:
        return JsonResponse(settings.PYLOAD.stop_downloads())
    except:
        return HttpResponseServerError()

@permission('pyload.can_see_dl')
def packages(request):
    try:
        data = settings.PYLOAD.get_queue()
        
        for package in data:
            package['links'] = []
            for file in settings.PYLOAD.get_package_files(package['id']):
                package['links'].append(settings.PYLOAD.get_file_info(file))
        
        return JsonResponse(data)
        
    except:
        return HttpResponseServerError()

@permission('pyload.can_see_dl')
def package(request, id):
    try:
        data = settings.PYLOAD.get_package_data(int(id))
        data['links'] = []
        for file in settings.PYLOAD.get_package_files(data['id']):
            data['links'].append(settings.PYLOAD.get_file_info(file))

        return JsonResponse(data)
        
    except:
        return HttpResponseServerError()
        
@permission('pyload.can_see_dl')
def link(request, id):
    try:
        data = settings.PYLOAD.get_file_info(int(id))
        return JsonResponse(data)
        
    except:
        return HttpResponseServerError()

@permission('pyload.can_add_dl')
def remove_package(request, id):
    try:
        settings.PYLOAD.del_packages([int(id)])
        return JsonResponse("sucess")
    except:
        return HttpResponseServerError()

@permission('pyload.can_add_dl')
def restart_package(request, id):
    try:
        settings.PYLOAD.restart_package(int(id))
        return JsonResponse("sucess")
    except:
        return HttpResponseServerError()

@permission('pyload.can_add_dl')
def restart_link(request, id):
    try:
        settings.PYLOAD.restart_file(int(id))
        return JsonResponse("sucess")
    except:
        return HttpResponseServerError()
        
@permission('pyload.can_add_dl')
def abort_link(request, id):
    try:
        settings.PYLOAD.stop_download("link", int(id))
        return JsonResponse("sucess")
    except:
        return HttpResponseServerError()
        
@permission('pyload.can_add_dl')
def push_to_queue(request, id):
    try:
        settings.PYLOAD.push_package_2_queue(int(id))
        return JsonResponse("sucess")
    except:
        return HttpResponseServerError()