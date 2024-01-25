from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.views import View
from django.http import StreamingHttpResponse
from django.http import HttpResponse
from django.views.decorators.http import condition
import cv2
import imutils
import xml.etree.ElementTree as ET
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import requires_csrf_token
import requests
from requests.auth import HTTPDigestAuth
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from users_admin.settings import DEVICE_UUID, GATEWAY_USER, GATEWAY_PASSWORD, GATEWAY_RTSP, GATEWAY_PORT, GATEWAY_CAMERAS
from user_profile_api.urls_services import (
    URL_STREAM_101,
    URL_OPEN_DOOR_1,
    URL_SEARCH_USER,
    URL_AcsEvent,
    URL_UserRightWeekPlanCfg,
    URL_DOOR_1,
    URL_DOOR_LOCKTYPE,
)
import datetime
import json, base64
from django.http import JsonResponse
import hashlib
from .models import SubjectSchedule, Device
from django.db.models import F
import itertools
import subprocess

def check_admin(user):
   return user.is_superuser

# Archivo de vistas. Se activan funcionalidades que corresponden a vistas con plantillas
# personalizadas y que no están ligadas directamente con el panel por defecto de Django.

# Vista con plantilla de la funcionalidad visualizar vídeo. Se obtienen identificadores de los
# diferentes dispositivos para que luega pueda ser generado el enlace
# necesario  al verse las cámaras con go2rtc.

@user_passes_test(check_admin)
def video(request):
    objetos = Device.objects.all()
    devices = [objeto.device for objeto in objetos]  

    link = GATEWAY_CAMERAS
    src_params = [f'src={device}' for device in devices]
    link += '&'.join(src_params)
    link += '&mode=webrtc'

    context = {
        'link': link,
        'devices': devices
    }

    return render(request, "custom/video/video.html", context)

# Vista de la funcionalidad para abrir la puerta asignada a un dispositivo. 
# Se activa con el pulsado de botón en una vista con plantilla anterior y
# envía un JSON respectivo.

@user_passes_test(check_admin)
def video_open_door(request, device):
    print(device)
    ip = Device.objects.filter(device=device).values_list('ip', flat=True).first()

    base_url = "http://" + ip + ":85"
    door_url = f"{URL_OPEN_DOOR_1}?format=xml"
    url = f"{base_url}{door_url}"
    print(url)
    payload = "<RemoteControlDoor xmlns=\"http://www.isapi.org/ver20/XMLSchema\" version=\"2.0\"><cmd>open</cmd></RemoteControlDoor>"
    headers = {
        'Content-Type': 'application/xml'
    }
    response = requests.put(url, headers=headers, data=payload, auth=requests.auth.HTTPDigestAuth(GATEWAY_USER, GATEWAY_PASSWORD))
    return HttpResponse('')


# Vista de la funcionalidad para modificar los parámetros de una puerta asignada a un
# dispositivo. Se activa con el pulsado de un botón en una vista (show_doors) con plantilla 
# anterior y se envía un JSON respectivo.

class GetDoorsView(TemplateView):
    template_name = 'custom/show_doors/show_doors.html'

    def post(self, request, device, *args, **kwargs):

        doorName = request.POST.get('doorName')
        magneticType = request.POST.get('magneticType')
        openButtonType = request.POST.get('openButtonType')
        LockType_status = request.POST.get('LockType_status')
        openDuration = request.POST.get('openDuration')
        disabledOpenDuration = request.POST.get('disabledOpenDuration')
        magneticAlarmTimeout = request.POST.get('magneticAlarmTimeout')
        leaderCardOpenDuration = request.POST.get('leaderCardOpenDuration')

        ip = Device.objects.filter(device=device).values_list('ip', flat=True).first()

        base_url = "http://" + ip + ":85"
        door_url = f"{URL_DOOR_1}?format=xml"
        url = f"{base_url}{door_url}"
        print(url)
        payload_template = "<DoorParam xmlns=\"http://www.isapi.org/ver20/XMLSchema\" version=\"2.0\"><doorName>{}</doorName><magneticType>{}</magneticType><openButtonType>{}</openButtonType><openDuration>{}</openDuration><disabledOpenDuration>{}</disabledOpenDuration><magneticAlarmTimeout>{}</magneticAlarmTimeout><enableLeaderCard>false</enableLeaderCard><leaderCardOpenDuration>{}</leaderCardOpenDuration></DoorParam>"

        payload = payload_template.format(doorName, magneticType, openButtonType, openDuration, disabledOpenDuration, magneticAlarmTimeout, leaderCardOpenDuration)
        headers = {
            'Content-Type': 'application/xml'
        }
        response = requests.put(url, headers=headers, data=payload, auth=requests.auth.HTTPDigestAuth(GATEWAY_USER, GATEWAY_PASSWORD))
        
        base_url = "http://" + ip + ":85"
        door_url = f"{URL_DOOR_LOCKTYPE}?format=json"
        url = f"{base_url}{door_url}"
        print(url)
        payload = json.dumps({
            "LockType": {
                "status": LockType_status
            }
        })

        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.put(url, headers=headers, data=payload, auth=requests.auth.HTTPDigestAuth(GATEWAY_USER, GATEWAY_PASSWORD))

        
        return JsonResponse({})

# Vista de la funcionalidad para modificar los parámetros de una puerta asignada a un
# dispositivo. Se ejecuta al visualizar la plantilla directamente. Si ya existen
# valores cargados en el dispositivo se muestran y en caso de que no, no se
# muestran valores en los campos.

@user_passes_test(check_admin)
def show_doors(request, device):
    print(device)
    ip = Device.objects.filter(device=device).values_list('ip', flat=True).first()
    print(ip)

    base_url = "http://" + ip + ":85"
    record_url = f"{URL_DOOR_1}"
    full_url = f"{base_url}{record_url}"

    headers = {"Content-type": "application/xml"}

    try:
        response = requests.get(full_url, headers=headers, auth=requests.auth.HTTPDigestAuth(GATEWAY_USER, GATEWAY_PASSWORD))

        if response.status_code == 200:
            root = ET.fromstring(response.text)
            doorName = root.find('./{http://www.isapi.org/ver20/XMLSchema}doorName').text
            magneticType = root.find('./{http://www.isapi.org/ver20/XMLSchema}magneticType').text
            openButtonType = root.find('./{http://www.isapi.org/ver20/XMLSchema}openButtonType').text
            openDuration = root.find('./{http://www.isapi.org/ver20/XMLSchema}openDuration').text
            disabledOpenDuration = root.find('./{http://www.isapi.org/ver20/XMLSchema}disabledOpenDuration').text
            magneticAlarmTimeout = root.find('./{http://www.isapi.org/ver20/XMLSchema}magneticAlarmTimeout').text
            enableLeaderCard = root.find('./{http://www.isapi.org/ver20/XMLSchema}enableLeaderCard').text
            leaderCardOpenDuration = root.find('./{http://www.isapi.org/ver20/XMLSchema}leaderCardOpenDuration').text

            base_url = "http://" + ip + ":85"
            record_url = f"{URL_DOOR_LOCKTYPE}"
            full_url = f"{base_url}{record_url}"

            headers = {"Content-type": "application/json"}

            response = requests.get(full_url, headers=headers, auth=requests.auth.HTTPDigestAuth(GATEWAY_USER, GATEWAY_PASSWORD))

            data = json.loads(response.text)

            status = data["LockType"]["status"]

            context = {
                'device': device,
                'doorName': doorName,
                'magneticType': magneticType,
                'openButtonType': openButtonType,
                'openDuration': openDuration,
                'disabledOpenDuration': disabledOpenDuration,
                'magneticAlarmTimeout': magneticAlarmTimeout,
                'enableLeaderCard': enableLeaderCard,
                'leaderCardOpenDuration': leaderCardOpenDuration,
                'LockType_status': status,
            }

            return render(request, "custom/show_doors/show_doors.html", context)
        else:
            print(f'Error en la solicitud: {response.status_code}')

    except requests.exceptions.RequestException as e:
        print(f'Error de conexión: {e}')



def get_users(request, device):
    ip = Device.objects.filter(device=device).values_list('ip', flat=True).first()
    base_url = "http://" + ip + ":85"
    record_url = f"{URL_SEARCH_USER}?format=json"
    full_url = f"{base_url}{record_url}"
    payload = json.dumps({
        "UserInfoSearchCond": {
        "searchID": "0",
        "searchResultPosition": 0,
        "maxResults": 1500
        }
        })
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.post(full_url, headers=headers, data=payload, auth=requests.auth.HTTPDigestAuth(GATEWAY_USER, GATEWAY_PASSWORD))
    users = response.json()
    return JsonResponse({'users': users['UserInfoSearch']['UserInfo']})


class GetEventsView(TemplateView):
    template_name = 'custom/show_events/show_events.html'

    def post(self, request, device, *args, **kwargs):
        ip = Device.objects.filter(device=device).values_list('ip', flat=True).first()
        base_url = "http://" + ip + ":85"
        record_url = f"{URL_AcsEvent}?format=json"
        full_url = f"{base_url}{record_url}"

        usuario = request.POST.get('usuario', "")
        grupoevento = request.POST.get('grupoevento', "")
        tipoevento = request.POST.get('tipoevento', "")
        desde = request.POST.get('desde', "")
        hasta = request.POST.get('hasta', "")

        if grupoevento != "":
            grupoevento = int(grupoevento)
        if tipoevento != "":
            tipoevento = int(tipoevento)

        print("Datos: ")
        print(usuario)
        print(grupoevento)
        payload = {
            "AcsEventCond": {
                "searchID": "1",
                "searchResultPosition": 0,
                "maxResults": 500,
                "major": grupoevento,
                "minor": tipoevento,
                "startTime": desde,
                "endTime": hasta
            }
        }

        headers = {
        'Content-Type': 'application/json'
        }

        payload_json = json.dumps(payload)
        print(payload_json)
        response = requests.post(full_url, headers=headers, data=payload_json, auth=requests.auth.HTTPDigestAuth(GATEWAY_USER, GATEWAY_PASSWORD))
        events = response.json()
        print(response.text)
        if events['AcsEvent']['responseStatusStrg'] == 'NO MATCH':
            return JsonResponse({})
        else:
            return JsonResponse({'events': events['AcsEvent']['InfoList']})


@user_passes_test(check_admin)
def show_doors_devices(request):
    dispositivos = Device.objects.values_list('device', flat=True).distinct()
    lista_dispositivos = {'dispositivos': dispositivos}
    return render(request, 'custom/show_doors/show_devices.html', lista_dispositivos)


@user_passes_test(check_admin)
def schedule_career(request, career, year):
    datos = SubjectSchedule.objects.filter(
        career_subject_year__career__name_career=career,
        career_subject_year__year=year
    ).annotate(
        materia=F('career_subject_year__subject__subject')
    )
    print(datos)
    horas = ['17:00', '17:30', '18:00', '18:30', '19:00', '19:30', '20:00', '20:30', '21:00', '21:30', '22:00', '22:30', '23:00']
    dias = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    tabla = []
    for hora in horas:
        fila = [hora]
        for dia in dias:
            materias = []
            for dato in datos:
                if dato.begin_time.strftime('%H:%M') == hora and dia in dato.day or dato.end_time.strftime('%H:%M') == hora and dia in dato.day:
                    materias.append(dato.materia)
                materia = ", ".join(materias) if len(materias) > 1 else materias[0] if len(materias) == 1 else ''
            fila.append(materia)
        tabla.append(fila)
    return render(request, 'custom/horario/horario.html', {'tabla': tabla, 'career': career})


@user_passes_test(check_admin)
def schedule_career_home(request):
    carreras = SubjectSchedule.objects.values_list('career_subject_year__career__name_career', flat=True).distinct()
    lista_carreras = {'carreras': carreras}
    return render(request, 'custom/horario/horario_home.html', lista_carreras)


@user_passes_test(check_admin)
def schedule_career_home_year(request, career):
    years = SubjectSchedule.objects.filter(career_subject_year__career__name_career=career).values_list('career_subject_year__year', 'career_subject_year__career__name_career').distinct()
    lista_years = {'years': years}
    return render(request, 'custom/horario/horario_home_year.html', lista_years)


@user_passes_test(check_admin)
def show_users_devices(request):
    dispositivos = Device.objects.values_list('device', flat=True).distinct()
    lista_dispositivos = {'dispositivos': dispositivos}
    return render(request, 'custom/show_users/show_devices.html', lista_dispositivos)


@user_passes_test(check_admin)
def show_users(request, device):
    print(device)
    lista_device = {'device': device}
    return render(request, "custom/show_users/show_users.html", lista_device)


@user_passes_test(check_admin)
def show_events_devices(request):
    dispositivos = Device.objects.values_list('device', flat=True).distinct()
    lista_dispositivos = {'dispositivos': dispositivos}
    return render(request, 'custom/show_events/show_devices.html', lista_dispositivos)

@user_passes_test(check_admin)
def show_events(request, device):
    print(device)
    lista_device = {'device': device}
    return render(request, "custom/show_events/show_events.html", lista_device)