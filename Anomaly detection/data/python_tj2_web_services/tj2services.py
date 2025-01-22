# -*- coding: utf-8 -*-

"""Access to TJ-II Web services.
"""

import json
import requests
import warnings
from collections.abc import Sequence
import urllib.parse
import datetime as dt

version = '1.0'

HEADERS = {'User-Agent': f'python-tj2services/{version} ({requests.utils.default_user_agent()})'}

BASE_URL = 'https://info.fusion.ciemat.es/cgi-bin/TJII_{script}.cgi'

SERVICES_INFO = [('getlist', 'getlist', None, ('shot',), 'Obtaining the list of available signals for a given discharge.'), ('getdata', 'getdata', None, ('shot', 'signal'), 'Reading the time trace of a given signal.'), ('getprof', 'getprof', None, ('shot', 'signal'), 'Reading a given profile.'), ('getrdb_shots', 'getrdb', None, ('variables', 'shots'), 'Retrieving database parameters for a range of shots. "variables" can be a string or a list of strings; and "shots", a pulse number or a sequence of two shots (shot_min, shot_max).'), ('getrdb_dates', 'getrdb', None, ('variables', 'dates'), 'Retrieving database parameters for a range of dates. "variables" can be a string or a list of strings; and "dates", a date or a sequence of two dates (date_min, date_max). Date can be a string ("YYYYDDMM" or "Y-M-D") or a datetime.date instance.'), ('flux_cyl', 'getmagn', 'flux_cyl', ('config', 'r', 'phi', 'z'), 'To obtain the normalized magnetic flux, cylindrical coordinates.'), ('flux_car', 'getmagn', 'flux_car', ('config', 'x', 'y', 'z'), 'To obtain the normalized magnetic flux, cartesian coordinates.'), ('grad_flux_cyl', 'getmagn', 'grad_flux_cyl', ('config', 'r', 'phi', 'z'), 'To obtain the gradient of the flux magnetic field, cylindrical coordinates.'), ('grad_flux_car', 'getmagn', 'grad_flux_car', ('config', 'x', 'y', 'z'), 'To obtain the gradient of the flux magnetic field, cartesian coordinates.'), ('flux_surf_cyl', 'getmagn', 'flux_surf_cyl', ('config', 'psi', 'theta', 'phi'), 'To convert magnetic flux coordinates to cylindrical coordinates.'), ('flux_surf_car', 'getmagn', 'flux_surf_car', ('config', 'psi', 'theta', 'phi'), 'To convert magnetic flux coordinates to cartesian coordinates.'), ('b_field_cyl', 'getmagn', 'b_field_cyl', ('config', 'r', 'phi', 'z'), 'To obtain the magnetic field, cylindrical coordinates.'), ('b_field_car', 'getmagn', 'b_field_car', ('config', 'x', 'y', 'z'), 'To obtain the magnetic field, cartesian coordinates.'), ('grad_b_cyl', 'getmagn', 'grad_b_cyl', ('config', 'r', 'phi', 'z'), 'To obtain the gradient of the absolute magnetic field, cylindrical coordinates.'), ('grad_b_car', 'getmagn', 'grad_b_car', ('config', 'x', 'y', 'z'), 'To obtain the gradient of the absolute magnetic field, cartesian coordinates.'), ('iota', 'getmagn', 'iota', ('config', 'psi'), 'To obtain the rotational transform.'), ('iota_cyl', 'getmagn', 'iota_cyl', ('config', 'r', 'phi', 'z'), 'To obtain the rotational transform, cylindrical coordinates.'), ('iota_car', 'getmagn', 'iota_car', ('config', 'x', 'y', 'z'), 'To obtain the rotational transform, cartesian coordinates.'), ('volume', 'getmagn', 'volume', ('config', 'psi'), 'To obtain the volume.'), ('volume_cyl', 'getmagn', 'volume_cyl', ('config', 'r', 'phi', 'z'), 'To obtain the volume, cylindrical coordinates.'), ('volume_car', 'getmagn', 'volume_car', ('config', 'x', 'y', 'z'), 'To obtain the volume, cartesian coordinates.'), ('surface', 'getmagn', 'surface', ('config', 'psi'), 'To obtain the surface.'), ('surface_cyl', 'getmagn', 'surface_cyl', ('config', 'r', 'phi', 'z'), 'To obtain the volume, cylindrical coordinates.'), ('surface_car', 'getmagn', 'surface_car', ('config', 'x', 'y', 'z'), 'To obtain the volume, cartesian coordinates.'), ('configlist', 'getmagn', 'configlist', (), 'To obtain a list of available configurations.'), ('tj2', 'getmagn', 'tj2', ('phi',), 'To obtain the contour of the vacuum vessel at a given phi.')]  # noqa: E501


def is_sequence(obj):
    if isinstance(obj, str):
        return False
    return isinstance(obj, Sequence)


def date_to_str(x):
    if isinstance(x, dt.date):
        x = x.strftime("%Y%m%d")
    else:
        x = str(x)
        if '-' in x:
            tokens = x.split('-')
            if len(tokens) == 3:
                x = '{0:04d}{1:02d}{2:02d}'.format(*[int(z) for z in tokens])

    return x


def factory(funcname, script, functparam, params, doc):
    sparams = set(params)
    url = BASE_URL.format(script=script)

    def f(**kwargs):
        skw = set(kwargs)

        l1 = list(skw - sparams)
        if l1:
            raise TypeError(f"{funcname}() got an unexpected keyword argument '{l1[0]}'")

        l2 = list(sparams - skw)
        if l2:
            raise TypeError(f"{funcname}() missing required keyword argument: '{l2[0]}'")

        payload = []
        if functparam is not None:
            payload.append(('funct', functparam))
        for k, v in kwargs.items():
            try:
                if k == 'shot':
                    v = int(v)
                elif k in ['config', 'signal']:
                    v = str(v)
                elif k in ['variables']:
                    if not is_sequence(v):
                        v = [v]
                    v = [str(x) for x in v]
                    v = ','.join(v)
                elif k in ['shots']:
                    if not is_sequence(v):
                        v = [v]
                    v = [str(int(x)) for x in v]
                    v = ','.join(v)
                elif k in ['dates']:
                    if not is_sequence(v):
                        v = [v]
                    v = [date_to_str(x) for x in v]
                    v = ','.join(v)
                else:
                    v = float(v)
            except ValueError:
                raise ValueError(f"Wrong value for '{k}'")

            payload.append((k, str(v)))

        # To skip , -> %2C conversion
        payload_str = urllib.parse.urlencode(payload, safe=',')

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = requests.get(url, params=payload_str, timeout=30, verify=False, headers=HEADERS)

        if r.ok:
            text = r.text
            # Work around
            text = text.replace('\n', '').replace('\x00', '')
            result = json.loads(text)

            if (funcname.startswith('getrdb_') and
                    not (len(result) == 1 and 'error' in result[0])):
                # getrdb_ and not error
                result = {'error': '', 'info': result}
            else:
                # not getrdb_ or error
                result = result[0]
        else:
            result = {'error': f'Bad web response ({r.status_code})'}

        return result

    argsdoc = ', '.join(params)
    if argsdoc:
        argsdoc = '*, ' + argsdoc
    fulldoc = f'{funcname}({argsdoc})\n\n{doc}'
    f.__doc__ = fulldoc
    f.__name__ = funcname

    return f


for funcname, script, functparam, params, doc in SERVICES_INFO:
    globals()[funcname] = factory(funcname, script, functparam, params, doc)


del funcname, script, functparam, params, doc, factory
