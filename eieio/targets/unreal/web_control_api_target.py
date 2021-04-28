import requests
import json
from eieio.measurement.log import LogEvent

HTTP_PORT = 30010
REQUEST_TIMEOUT = 5

RETRIEVE_OR_SET_PROPERTY_ENDPOINT = 'remote/object/property'
CALL_REMOTE_FUNCTION_ENDPOINT = 'remote/object/call'

THIRD_PERSON_DEMO_HOST = '192.168.1.56'
THIRD_PERSON_DEMO_OBJECT_PATH = '/Game/ThirdPersonBP/Maps/ThirdPersonExampleMap.ThirdPersonExampleMap:PersistentLevel' \
                                '.LightSource_0.LightComponent0'
THIRD_PERSON_DEMO_PROPERTY_NAME = 'RelativeRotation'

CALMAP_OBJECT = '/Game/CalMap.CalMap:PersistentLevel.color_cal_character_2'
CALMAP_PROPERTY_NAME = 'input_color'
# CALMAP_FUNCTION_NAME = 'DoUpdate'


class UnrealWebControlApiTarget(object):
    def __init__(self, host, port=HTTP_PORT, timeout=REQUEST_TIMEOUT, debug=False):
        self._host = None
        self.host = host
        self._port = None
        self.port = port
        self._timeout = None
        self.timeout = timeout
        self._debug = False
        self.debug = debug

    @property
    def host(self):
        return self._host

    @host.setter
    def host(self, value):
        self._host = value

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, value):
        self._port = value

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        self._timeout = value

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        self._debug = value

    def _url(self, endpoint):
        return f"http://{self.host}:{self.port}/{endpoint}"

    def _headers(self):
        return {'User-Agent': __file__,
                'Content-Type': 'application/json',
                'Accept': '*/*',
                'Referer': f"http://{self.host}",
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'en-us,en;q=0.9'}

    def _request(self, url, headers, body):
        if self.debug:
            print()
            print(f"outgoing URL: `{url}'")
            print(f"outgoing headers: `{headers}'")
            print(f"outgoing body: `{body}'")
            print(f"outgoing timeout (sec): {self.timeout}")
        response = requests.put(url, headers=headers, data=body, timeout=self.timeout)
        if self.debug:
            print(f"response: `{response.text}'")

    @staticmethod
    def _retrieve_remote_property_body(object_path, property_name):
        return json.dumps({"objectPath": object_path,
                           'access': 'READ_ACCESS',
                           'propertyName': property_name})

    def retrieve_remote_property(self, object_path, property_name):
        url = self._url(RETRIEVE_OR_SET_PROPERTY_ENDPOINT)
        headers = self._headers()
        body = UnrealWebControlApiTarget._retrieve_remote_property_body(object_path, property_name)
        return self._request(url, headers, body)

    @staticmethod
    def _set_remote_property_body(object_path, property_name, property_value):
        return json.dumps({"objectPath": object_path,
                           'access': 'WRITE_TRANSACTION_ACCESS',
                           'propertyName': property_name,
                           'propertyValue': property_value})

    def set_remote_property(self, object_path, property_name, property_value):
        url = self._url(RETRIEVE_OR_SET_PROPERTY_ENDPOINT)
        headers = self._headers()
        body = UnrealWebControlApiTarget._set_remote_property_body(object_path, property_name, property_value)
        print(f"body is `{body}'")
        return self._request(url, headers, body)

    @staticmethod
    def _call_remote_function_body(object_path, function_name, parameter_dict=None):
        # replace with the idiom I'm forgetting
        body_dict = dict() if not parameter_dict else parameter_dict
        if 'objectPath' in body_dict:
            raise RuntimeError('objectPath must be an argument, not a parameter')
        if 'functionName' in body_dict:
            raise RuntimeError('functionName must be an argument, not a parameter')
        body_dict['objectPath'] = object_path
        body_dict['functionName'] = function_name
        body_dict['generateTransaction'] = True
        return json.dumps(body_dict)

    def call_remote_function(self, object_path, function_name, **kwargs):
        url = self._url(CALL_REMOTE_FUNCTION_ENDPOINT)
        headers = self._headers()
        body = UnrealWebControlApiTarget._call_remote_function_body(object_path, function_name, kwargs)
        return self._request(url, headers, body)

    def set_target_stimulus(self, _, rgb, log=None,
                            object_path=CALMAP_OBJECT,
                            remote_property_name=CALMAP_PROPERTY_NAME):
        # value_string = f"{{'R':{rgb[0]},'G':{rgb[1]},'B':{rgb[2]},'A':1}}"
        # property_value = {'input_color': value_string}
        if log:
            log.add(LogEvent.OPTION_SETTING,
                    f"about to set web control api target 'input_color' property "
                    f"to {rgb[0]:.3f}, {rgb[1]:.3f} {rgb[2]:.3f}")
        property_value = {'input_color': {'R': rgb[0], 'G': rgb[1], 'B': rgb[2], 'A': 1}}
        self.set_remote_property(object_path, remote_property_name, property_value)
        # self.call_remote_function(object_path, 'DoUpdate')


if __name__ == '__main__':
    target = UnrealWebControlApiTarget(THIRD_PERSON_DEMO_HOST)
    target.debug = True
    target.retrieve_remote_property(THIRD_PERSON_DEMO_OBJECT_PATH, THIRD_PERSON_DEMO_PROPERTY_NAME)
    target.call_remote_function(THIRD_PERSON_DEMO_OBJECT_PATH, 'SetRelativeRotation',
                                parameters=json.dumps({'NewRotation': {'Pitch': 90, 'Yaw': 0, 'Roll': 0}}))
