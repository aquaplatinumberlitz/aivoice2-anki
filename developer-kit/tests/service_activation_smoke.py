#!/usr/bin/env python3
"""Opt-in real user-service smoke. Creates and cleans only a unique test unit/prefix.

Does not install an addon, create a desktop shortcut, open Anki or stop the
existing production service. Requires explicit --allow-user-service.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/setup'))
from install_core import install_files,initialize_runtime,sha
from integrations import activate,instance_id
from runtime_config import load_config


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--payload',type=Path,required=True)
    parser.add_argument('--msi',type=Path,required=True)
    parser.add_argument('--assets-dir',type=Path,required=True)
    parser.add_argument('--allow-user-service',action='store_true',required=True)
    args=parser.parse_args()
    (ROOT/'cache').mkdir(exist_ok=True)
    run=Path(tempfile.mkdtemp(prefix='service-check-',dir=ROOT/'cache'));target=run/'bản cài riêng'
    print('RUN_DIR',run,flush=True)
    name='aivoice2-local-'+instance_id(target)+'.service'
    info=None;config=None
    # Isolate cache/log/state as well as the Wine prefixes for this test.
    os.environ.update(XDG_CACHE_HOME=str(run/'xdg-cache'),XDG_STATE_HOME=str(run/'xdg-state'))
    try:
        config_path=install_files(args.msi,args.assets_dir/'Lang',args.assets_dir/'voicebanks',
            ['KotonohaAoi_ns_48'],target,args.payload,report=print)
        initialize_runtime(config_path,report=print)
        info=activate(target,enable_service=True,desktop=False,report=print)
        config=load_config(config_path)
        with urllib.request.urlopen(config.api_url+'/v1/voices',timeout=10) as response:
            voices=json.load(response)['voices']
        assert len(voices)==1 and voices[0]['folder']=='KotonohaAoi_ns_48'
        with urllib.request.urlopen(config.api_url+'/healthz',timeout=10) as response:health=json.load(response)
        assert health['ready'] and health['instance_id']==config.instance_id
        result={'passed':True,'scope':'Real owned user service; no Anki/desktop changes',
                'port':config.port,'production_17862_untouched':config.port!=17862,'health':health,'voices':len(voices)}
        (run/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    finally:
        # Prefixes and unit names are derived solely from this newly created root.
        record=target/'integration.json'
        if record.is_file():
            owned=json.loads(record.read_text())
            if owned.get('unit_name')==name:
                subprocess.run(['systemctl','--user','disable','--now',name],capture_output=True,timeout=30)
                unit=Path(owned['unit_path'])
                if unit.is_file() and sha(unit)==owned.get('unit_sha256'):unit.unlink()
                subprocess.run(['systemctl','--user','daemon-reload'],check=True)
        if (target/'config/runtime.json').is_file():
            config=load_config(target/'config/runtime.json')
            for prefix in [config.engine_prefix,config.gui_prefix]:
                subprocess.run(['wineserver','-k'],env=dict(os.environ,WINEPREFIX=str(prefix)),capture_output=True,timeout=15)


if __name__=='__main__':main()
