from django.db.models.signals import post_save, pre_save, pre_delete, post_delete, m2m_changed
from django.dispatch import receiver
import requests
import yaml
import json, base64
from datetime import datetime
from user_profile_api.middleware import specific_page_loaded

from user_profile_api.urls_services import (
    URL_RECORD_USER,
    URL_DELETE_USER,
    URL_SEARCH_USER,
    URL_MODIFY_USER,
    URL_RECORD_CARD,
    URL_DELETE_CARD,
    URL_COUNT_USER,
    URL_RECORD_IMAGE,
    URL_UserRightWeekPlanCfg,
    URL_FaceDataRecord,
)
from users_admin.settings import DEVICE_UUID, GATEWAY_USER, GATEWAY_PASSWORD, GATEWAY_PORT
from requests.auth import HTTPDigestAuth
from user_profile_api.models import UserProfile, SubjectSchedule, Device
from user_profile_api.services import get_default_user_device_id
from django.db.models import F
from unidecode import unidecode

# Archivo de señales. Se activan funcionalidades que están ligadas al panel de administración
# que trae por defecto Django basandose en detección de cambios en los modelos 
# localizados en models.py

# Se cambia el booleano para comprobar funcionalidades sin necesidad
# de tener conectado un dispositivo

mockeo = False

# Señal que se acciona al detectar un cambio en las relaciones M2M de la tabla
# UserProfile. Se ejecuta si se carga un usuario relacionado a ciertos horarios.
# En el código se filtra según los dispositivos que están relacionados con los horarios asignados,
# y por cada uno de ellos se envía el JSON para localizar al usuario. 
# Dependiendo del condicional se crea o modifica el usuario con o sin imagen.

@receiver(m2m_changed, sender=UserProfile.subject.through)
def update_user_subjects(sender, instance, action, pk_set, **kwargs):
    if action == "pre_add" or action == "pre_remove":

        if mockeo:
            return

        subject_ids = list(pk_set)
        subject_schedules = SubjectSchedule.objects.filter(pk__in=subject_ids)
        device_ips = list(Device.objects.filter(subjectschedule__in=subject_schedules).values_list('ip', flat=True).distinct())

        print("subject_ids")
        print(subject_ids)
        print("subject_schedules")
        print(subject_schedules)


        print("Probando:")
        print(device_ips)
        print("Cantidad de valores:", len(device_ips))

        for i in range(len(device_ips)):


            print("Iteración:", i)
            ip_seleccionada = device_ips.pop(0)
            print(ip_seleccionada)
            print(device_ips)

            print("Filtrar con IP")

            filtered_horario_ids = list(subject_schedules.filter(device__ip=ip_seleccionada).values_list('horario_id', flat=True))
            days = list(subject_schedules.filter(device__ip=ip_seleccionada).values_list('day', flat=True))


            print(filtered_horario_ids)
            print(days)

            base_url = "http://{}:{}".format(ip_seleccionada, GATEWAY_PORT)
            record_url = f"{URL_SEARCH_USER}?format=json"
            full_url = f"{base_url}{record_url}"
            headers = {"Content-type": "application/json"}

            data = {
            "UserInfoSearchCond":
                {
                    "searchID": str(instance.user_device_id),
                    "searchResultPosition":0,
                    "maxResults":1,
                    "EmployeeNoList": [{
                        "employeeNo": str(instance.user_device_id)
                    }]
                }
            }

            response = requests.post(
                    full_url,
                    headers=headers,
                    data=json.dumps(data),
                    auth=HTTPDigestAuth(GATEWAY_USER, GATEWAY_PASSWORD),
            )

            

            response_json = json.loads(response.text)
            response_status = response_json["UserInfoSearch"]["responseStatusStrg"]
            print(response_status)




            if response_status == "NO MATCH" and not action == "pre_remove":

                subject_ids = list(filtered_horario_ids)
                plan_template_no = ','.join(map(str, subject_ids))

                print("Testeando")
                print(plan_template_no)

                base_url = "http://{}:{}".format(ip_seleccionada, GATEWAY_PORT)
                record_url = f"{URL_RECORD_USER}?format=json"
                full_url = f"{base_url}{record_url}"
                headers = {"Content-type": "application/json"}

                begin_time_str = instance.beginTime.strftime("%Y-%m-%dT%H:%M:%S")
                end_time_str = instance.endTime.strftime("%Y-%m-%dT%H:%M:%S")

                data = {
                    "UserInfo": 
                        {
                            "employeeNo": str(instance.user_device_id),
                            "name": str(instance.first_name + " " + instance.last_name),
                            "userType": instance.profile_type,
                            "gender": instance.gender,
                            "Valid": {
                                "enable": instance.is_active,
                                "beginTime": begin_time_str,
                                "endTime": end_time_str,
                                "timeType": instance.timeType
                            },
                            "doorRight": instance.doorRight,
                            "RightPlan": [
                                {
                                    "doorNo": instance.doorNo,
                                    "planTemplateNo": plan_template_no
                                }
                            ],
                            "localUIRight": instance.is_staff,
                            "userVerifyMode": instance.userVerifyMode
                        }
                    }

                response = requests.post(
                    full_url,
                    headers=headers,
                    data=json.dumps(data),
                    auth=HTTPDigestAuth(GATEWAY_USER, GATEWAY_PASSWORD),
                )

                if response.status_code == 200:
                        print("Usuario creado y cargado con la API y CAMPO")
                        if instance.fileImage:

                            ips = []

                            for subject_schedule in subject_schedules:
                                device = subject_schedule.device
                                if device and device.is_active:  
                                    ips.append(device.ip)

                            print(ips)

                            for ip_address in ips:
                                
                                base_url = f'http://{ip_address}:{GATEWAY_PORT}'
                                record_url = f"{URL_RECORD_IMAGE}?format=json"
                                full_url = f"{base_url}{record_url}"
                                    
                                print("Acá es 1")

                                payload = {
                                    "FaceDataRecord": ('', '{"faceLibType":"blackFD","FDID":"1","FPID":"' + str(instance.user_device_id) + '"}', 'application/json'),
                                    "img": ('Imagen', open(str(instance.fileImage), 'rb'), 'image/jpeg')
                                }

                                print(payload)


                                response = requests.put(full_url, files=payload, auth=HTTPDigestAuth(GATEWAY_USER, GATEWAY_PASSWORD))

                                if response.status_code == 200:
                                    print("Image created succesfully and sent to API!")
                                    print("User created successfully and data sent to API!")
                                else:
                                    raise Exception("Error enviando la imagen al dispositivo: {}".format(response.text))

                else:
                    raise Exception("Error enviando el usuario al dispositivo: {}".format(response.text))

            elif response_status == "OK" and not action == "pre_remove":

                subject_ids = list(filtered_horario_ids)
                plan_template_no_new = ','.join(map(str, subject_ids))

                plan_template_no = response_json['UserInfoSearch']['UserInfo'][0]['RightPlan'][0]['planTemplateNo']
                print(plan_template_no)
                print(plan_template_no_new)

                existing_set = set(plan_template_no.split(","))
                new_set = set(plan_template_no_new.split(","))

                combined_set = existing_set.union(new_set)

                plan_template_definitivo = ",".join(sorted(combined_set))

                print("Definitivo")

                print(plan_template_definitivo)

                if mockeo:
                    return

                base_url = "http://{}:{}".format(ip_seleccionada, GATEWAY_PORT)
                record_url = f"{URL_MODIFY_USER}?format=json"
                full_url = f"{base_url}{record_url}"
                headers = {"Content-type": "application/json"}

                begin_time_str = instance.beginTime.strftime("%Y-%m-%dT%H:%M:%S")
                end_time_str = instance.endTime.strftime("%Y-%m-%dT%H:%M:%S")

                data = {
                    "UserInfo": 
                        {
                            "employeeNo": str(instance.user_device_id),
                            "name": str(instance.first_name + " " + instance.last_name),
                            "userType": instance.profile_type,
                            "gender": instance.gender,
                            "Valid": {
                                "enable": instance.is_active,
                                "beginTime": begin_time_str,
                                "endTime": end_time_str,
                                "timeType": instance.timeType
                            },
                            "doorRight": instance.doorRight,
                            "RightPlan": [
                                {
                                    "doorNo": instance.doorNo,
                                    "planTemplateNo": plan_template_definitivo
                                }
                            ],
                            "localUIRight": instance.is_staff,
                            "userVerifyMode": instance.userVerifyMode
                        }
                    }

                response = requests.put(
                    full_url,
                    headers=headers,
                    data=json.dumps(data),
                    auth=HTTPDigestAuth(GATEWAY_USER, GATEWAY_PASSWORD),
                )


                if response.status_code == 200:
                    print("Usuario modificado y cargado por la API y CAMPO")
                else:
                    raise Exception("Failed to modify instance: {}".format(response.text))

            elif response_status == "OK" and action == "pre_remove":

                subject_ids = list(filtered_horario_ids)
                plan_template_no_new = ','.join(map(str, subject_ids))

                plan_template_no = response_json['UserInfoSearch']['UserInfo'][0]['RightPlan'][0]['planTemplateNo']
                print(plan_template_no)
                print(plan_template_no_new)

                existing_set = set(plan_template_no.split(","))
                new_set = set(plan_template_no_new.split(","))

                final_set = existing_set.difference(new_set)

                plan_template_definitivo = ",".join(sorted(final_set))

                print("Definitivo")

                print(plan_template_definitivo)

                if mockeo:
                    return

                base_url = "http://{}:{}".format(ip_seleccionada, GATEWAY_PORT)
                record_url = f"{URL_MODIFY_USER}?format=json"
                full_url = f"{base_url}{record_url}"
                headers = {"Content-type": "application/json"}

                begin_time_str = instance.beginTime.strftime("%Y-%m-%dT%H:%M:%S")
                end_time_str = instance.endTime.strftime("%Y-%m-%dT%H:%M:%S")

                data = {
                    "UserInfo": 
                        {
                            "employeeNo": str(instance.user_device_id),
                            "name": str(instance.first_name + " " + instance.last_name),
                            "userType": instance.profile_type,
                            "gender": instance.gender,
                            "Valid": {
                                "enable": instance.is_active,
                                "beginTime": begin_time_str,
                                "endTime": end_time_str,
                                "timeType": instance.timeType
                            },
                            "doorRight": instance.doorRight,
                            "RightPlan": [
                                {
                                    "doorNo": instance.doorNo,
                                    "planTemplateNo": plan_template_definitivo
                                }
                            ],
                            "localUIRight": instance.is_staff,
                            "userVerifyMode": instance.userVerifyMode
                        }
                    }

                response = requests.put(
                    full_url,
                    headers=headers,
                    data=json.dumps(data),
                    auth=HTTPDigestAuth(GATEWAY_USER, GATEWAY_PASSWORD),
                )


                if response.status_code == 200:
                    print("Usuario modificado y cargado por la API y CAMPO")
                else:
                    raise Exception("Failed to modify instance: {}".format(response.text))


# Señales que se activan después de agregar un dispositivo en la base de datos. 
# Crea, modifica o elimina la configuración en el directorio por lo que es necesario reiniciar el
# programa go2rtc para que los cambios sean efectuados.

@receiver(post_save, sender=Device)
def send_yaml_config(sender, instance, created, **kwargs):
    if created:
        ruta_archivo = 'go2rtc.yaml'

        with open(ruta_archivo, 'r') as archivo:
            contenido = yaml.safe_load(archivo)

        if not contenido['streams']:
            contenido['streams'] = {}

        if str(instance.device) not in contenido:
            contenido['streams'][str(instance.device)] = [
                f"rtsp://{GATEWAY_USER}:{GATEWAY_PASSWORD}@{instance.ip}:554/ISAPI/Streaming/Channels/101"
     #           f"isapi://admin:password@{instance.ip}:80/"
            ]

        with open(ruta_archivo, 'w') as archivo:
            yaml.dump(contenido, archivo)

        print("Contenido del archivo YAML agregado")

@receiver(pre_save, sender=Device)
def modify_yaml_config(sender, instance, **kwargs):
    if instance.pk:
        old_instance = Device.objects.get(pk=instance.pk)
        old_value = old_instance.device

        ruta_archivo = 'go2rtc.yaml'

        with open(ruta_archivo, 'r') as archivo:
            contenido = yaml.safe_load(archivo)

        if not contenido['streams']:
            contenido['streams'] = {}

        print(old_instance.device)
        print(instance.device)

        if str(old_instance.device) in contenido['streams']:
            del contenido['streams'][str(old_instance.device)]

            contenido['streams'][str(instance.device)] = [
                f"rtsp://{GATEWAY_USER}:{GATEWAY_PASSWORD}@{instance.ip}:554/ISAPI/Streaming/Channels/101"
     #           f"isapi://admin:password@{instance.ip}:80/"
            ]

        with open(ruta_archivo, 'w') as archivo:
            yaml.dump(contenido, archivo)

        print("Contenido del archivo YAML modificado")  



@receiver(post_delete, sender=Device)
def delete_yaml_config(sender, instance, **kwargs):
    ruta_archivo = 'go2rtc.yaml'

    with open(ruta_archivo, 'r') as archivo:
        contenido = yaml.safe_load(archivo)

    print(instance.device)
    if str(instance.device) in contenido['streams']:
        del contenido['streams'][str(instance.device)]

    with open(ruta_archivo, 'w') as archivo:
        yaml.dump(contenido, archivo)

    print("Contenido del archivo YAML eliminado")      

# Señal que se activa después de agregar de un usuario de la tabla UserProfile.
# Se envía un JSON dependiendo del condicional si se está creando o modificando.

@receiver(post_save, sender=UserProfile)
def send_user_data(sender, instance, created, **kwargs):
    if created:
        if mockeo:
            return

        if not instance.subject:

            subject_schedules = instance.subject.all()
            ips = []

            for subject_schedule in subject_schedules:
                device = subject_schedule.device
                if device and device.is_active:  
                    ips.append(device.ip)

            print(ips)

            for ip_address in ips:

                base_url = f'http://{ip_address}:{GATEWAY_PORT}'
                record_url = f"{URL_RECORD_USER}?format=json"
                full_url = f"{base_url}{record_url}"
                headers = {"Content-type": "application/json"}

                begin_time_str = instance.beginTime.strftime("%Y-%m-%dT%H:%M:%S")
                end_time_str = instance.endTime.strftime("%Y-%m-%dT%H:%M:%S")

                data = {
                    "UserInfo": 
                        {
                            "employeeNo": str(instance.user_device_id),
                            "name": str(instance.first_name + " " + instance.last_name),
                            "userType": instance.profile_type,
                            "gender": instance.gender,
                            "Valid": {
                                "enable": instance.is_active,
                                "beginTime": begin_time_str,
                                "endTime": end_time_str,
                                "timeType": instance.timeType
                            },
                            "doorRight": instance.doorRight,
                            "RightPlan": [
                                {
                                    "doorNo": instance.doorNo,
                                }
                            ],
                            "localUIRight": instance.is_staff,
                            "userVerifyMode": instance.userVerifyMode
                        }
                    }

                print("Probemos para ver device: ")
                print(instance.subject)

                response = requests.post(
                    full_url,
                    headers=headers,
                    data=json.dumps(data),
                    auth=HTTPDigestAuth(GATEWAY_USER, GATEWAY_PASSWORD),
                )

                if response.status_code == 200:
                        print("Usuario creado y cargado con la API (sin horario) 1")
                else:
                    raise Exception("Error enviando el usuario al dispositivo: {}".format(response.text))

    else:
        if mockeo:
            return

            
        previous_instance = UserProfile.objects.get(pk=instance.pk)

        previous_subject_ids = set(previous_instance.subject.values_list('pk', flat=True))
        current_subject_ids = set(instance.subject.values_list('pk', flat=True))

        if previous_subject_ids == current_subject_ids:

            subject_schedules = instance.subject.all()
            device_ips = list(subject_schedules.values_list('device__ip', flat=True).distinct())

            print("Probando:")
            print(device_ips)
            print("Cantidad de valores:", len(device_ips))

            for i in range(len(device_ips)):

                print("Iteración:", i)
                ip_seleccionada = device_ips.pop(0)
                print(ip_seleccionada)

                base_url = "http://{}:{}".format(ip_seleccionada, GATEWAY_PORT)
                record_url = f"{URL_MODIFY_USER}?format=json"
                full_url = f"{base_url}{record_url}"
                headers = {"Content-type": "application/json"}

                begin_time_str = instance.beginTime.strftime("%Y-%m-%dT%H:%M:%S")
                end_time_str = instance.endTime.strftime("%Y-%m-%dT%H:%M:%S")

                data = {
                    "UserInfo": 
                        {
                            "employeeNo": str(instance.user_device_id),
                            "name": str(instance.first_name + " " + instance.last_name),
                            "userType": instance.profile_type,
                            "gender": instance.gender,
                            "Valid": {
                                "enable": instance.is_active,
                                "beginTime": begin_time_str,
                                "endTime": end_time_str,
                                "timeType": instance.timeType
                            },
                            "doorRight": instance.doorRight,
                            "RightPlan": [
                                {
                                    "doorNo": instance.doorNo,
                                }
                            ],
                            "localUIRight": instance.is_staff,
                            "userVerifyMode": instance.userVerifyMode
                        }
                    }

                response = requests.put(
                    full_url,
                    headers=headers,
                    data=json.dumps(data),
                    auth=HTTPDigestAuth(GATEWAY_USER, GATEWAY_PASSWORD),
                )

                if response.status_code == 200:
                    print(response.text)
                    modificado = True 
                else:
                    modificado = False
                    mensaje1 = response.text
                    print("Mensaje 1")
                    print(mensaje1)

                    
            if not instance.fileImage:

                subject_schedules = instance.subject.all()
                ips = []

                for subject_schedule in subject_schedules:
                    device = subject_schedule.device
                    if device and device.is_active:  
                        ips.append(device.ip)

                print(ips)

                for ip_address in ips:
                    base_url = f'http://{ip_address}:{GATEWAY_PORT}'
                    record_url = f"{URL_RECORD_IMAGE}?format=json"
                    full_url = f"{base_url}{record_url}"

                    data = {
                        "faceLibType": "blackFD",
                        "FDID": "1",
                        "FPID": str(instance.user_device_id),
                        "deleteFP": True
                    }

                    print("Acá es 4")

                    print(data)


                    response = requests.put(full_url, data=json.dumps(data), auth=HTTPDigestAuth(GATEWAY_USER, GATEWAY_PASSWORD))


                    if response.status_code == 200:
                        imagen_borrada = True
                    else:
                        imagen_borrada = False
                        print("Mensaje 2")
                        mensaje2 = response.text

                    if response.status_code == 200:
                        print("Usuario modificado y cargado por la API (sin horario) 2")
                    else:
                        print(mensaje2)
                        raise Exception("Failed to modify instance: {}".format(response.text))

            

# Señal que se activa después de agregar un usuario en la tabla UserProfile. A diferencia
# de la señal anterior, se utiliza para sumar la imagen si es que se adjuntó alguna.

@receiver(post_save, sender=UserProfile)
def send_image_data(sender, created, instance, **kwargs):
        if created:
            return 
        else:
            original_instance = sender.objects.get(pk=instance.pk)
            if instance.fileImage != original_instance.fileImage:
                subject_schedules = instance.subject.all()
                ips = []

                for subject_schedule in subject_schedules:
                    device = subject_schedule.device
                    if device and device.is_active:  
                        ips.append(device.ip)

                print(ips)

                for ip_address in ips:

                    base_url = f'http://{ip_address}:{GATEWAY_PORT}'
                    record_url = f"{URL_RECORD_IMAGE}?format=json"
                    full_url = f"{base_url}{record_url}"

                    data = {
                        "faceLibType": "blackFD",
                        "FDID": "1",
                        "FPID": str(instance.user_device_id),
                        "deleteFP": True
                    }

                    print("Acá es 2")

                    print(data)


                    response = requests.request("PUT", full_url, data=json.dumps(data), auth=HTTPDigestAuth(GATEWAY_USER, GATEWAY_PASSWORD))


                    if response.status_code == 200:
                        print("Image deleted succesfully and sent to API!")
                        print("User deleted successfully and data sent to API!")
                    else:
                        raise Exception("Error enviando la imagen al dispositivo: {}".format(response.text))

            if instance.fileImage:

                subject_schedules = instance.subject.all()
                ips = []

                for subject_schedule in subject_schedules:
                    device = subject_schedule.device
                    if device and device.is_active:  
                        ips.append(device.ip)

                print(ips)

                for ip_address in ips:
                    base_url = f'http://{ip_address}:{GATEWAY_PORT}'
                    record_url = f"{URL_RECORD_IMAGE}?format=json"
                    full_url = f"{base_url}{record_url}"

                    print("Acá es 3")
                    

                    payload = {
                        "FaceDataRecord": ('', '{"faceLibType":"blackFD","FDID":"1","FPID":"' + str(instance.user_device_id) + '"}', 'application/json'),
                        "img": ('Imagen', open(str(instance.fileImage), 'rb'), 'image/jpeg')
                    }

                    print(payload)

                    response = requests.put(full_url, files=payload, auth=HTTPDigestAuth(GATEWAY_USER, GATEWAY_PASSWORD))

                    if response.status_code == 200:
                        print("Image created succesfully and sent to API!")
                        print("User created successfully and data sent to API!")
                    else:
                        raise Exception("Error enviando la imagen al dispositivo: {}".format(response.text))



# Se activa luego de cargar un horario de materia en la tabla SubjectSchedule.
# Se sube el JSON al dispositivo respectivo tanto como para el horario de la materia
# como el plan de horario relacionado.

@receiver(pre_save, sender=SubjectSchedule)
def enviar_horario(sender, instance, **kwargs):
    if mockeo:
        return

    ip = instance.device.ip

    subject_schedules = []
    id_mapping = {}

    unique_days = list(set(instance.day))

    for day in unique_days:
        if day not in id_mapping:
            id_mapping[day] = 1
        else:
            id_mapping[day] += 1

        subject_data = {
            "week": day,
            "id": id_mapping[day],
            "enable": True,
            "TimeSegment": {
                "beginTime": str(instance.begin_time),
                "endTime": str(instance.end_time)
            }
        }
        subject_schedules.append(subject_data)

    subject_schedules.sort(key=lambda x: x['week'])

    json_data = {
        "UserRightWeekPlanCfg": {
            "enable": True,
            "WeekPlanCfg": subject_schedules
        }
    }

    json_str = json.dumps(json_data, indent=4)

    print(json_str)
    print(instance.horario_id)

    base_url = "http://{}:{}".format(ip, GATEWAY_PORT)
    record_url = f"/ISAPI/AccessControl/UserRightWeekPlanCfg/{instance.horario_id}?format=json"
    full_url = f"{base_url}{record_url}"
    headers = {"Content-type": "application/json"}


    response = requests.put(
        full_url,
        headers=headers,
        data=json_str,
        auth=HTTPDigestAuth(GATEWAY_USER, GATEWAY_PASSWORD),
    )

    if response.status_code == 200:
        print("Se registró correctamente el horario!")

        base_url = "http://{}:{}".format(ip, GATEWAY_PORT)
        record_url = f"/ISAPI/AccessControl/UserRightPlanTemplate/{instance.horario_id}?format=json"
        full_url = f"{base_url}{record_url}"
        headers = {"Content-type": "application/json"}


        coded_value = str(instance.career_subject_year)
        decoded_value = unidecode(coded_value)
        subject = decoded_value.split(" - ")[1]

        json_data = {
            "UserRightPlanTemplate":{
                "enable": True,
                "templateName": subject,
                "weekPlanNo": instance.horario_id,
                "holidayGroupNo": ""
            }
        }

        json_str = json.dumps(json_data, indent=4)
        print(json_str)

        response = requests.put(
            full_url,
            headers=headers,
            data=json_str,
            auth=HTTPDigestAuth(GATEWAY_USER, GATEWAY_PASSWORD),
        )
        if response.status_code == 200:
            print("Se registró correctamente el template del horario!!")
        else:
            raise Exception("Error registrando el template de horario: {}".format(response.text))
    else:
        raise Exception("Error registrando el horario: {}".format(response.text))
    




@receiver(pre_delete, sender=UserProfile)
def delete_user_data(sender, instance, **kwargs):
    if mockeo:
            return

    pre_delete.disconnect(delete_user_data, sender=UserProfile)
    
    subject_schedules = instance.subject.all()
    ips = []

    for subject_schedule in subject_schedules:
        device = subject_schedule.device
        if device and device.is_active:  
            ips.append(device.ip)

    print(ips)

    for ip_address in ips:
        base_url = f'http://{ip_address}:{GATEWAY_PORT}'

        print(base_url)

        record_url = f"{URL_DELETE_USER}?format=json"
        full_url = f"{base_url}{record_url}"
        headers = {"Content-type": "application/json"}

        data = {
            "UserInfoDetail": {
                "mode": "byEmployeeNo",
                "EmployeeNoList": [{"employeeNo": str(instance.user_device_id)}],
            }
        }

        response = requests.put(
            full_url,
            headers=headers,
            data=json.dumps(data),
            auth=HTTPDigestAuth(GATEWAY_USER, GATEWAY_PASSWORD),
        )

        if response.status_code == 200:
            print("User deleted successfully!")
            instance.delete()
        else:
            print("Error: can't delete user")
            raise Exception("Failed to delete instance: {}".format(response.text))

        pre_delete.connect(delete_user_data, sender=UserProfile)
    



