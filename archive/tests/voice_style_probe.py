from pathlib import Path
import sys,os,subprocess,struct,json,hashlib,wave
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src/daemon'))
from run_auth_probe import credentials,windows_path,EDITOR
out=R/'notes/evidence/voice-identity';out.mkdir(exist_ok=True)
license_path=EDITOR/'Lib/AITalk/aitalk.lic';product,code=credentials(license_path)
for style in ['D:1', 'C:1', 'J:1']:
 label=style or 'default';log=(out/('probe-'+label+'.log')).open('wb')
 env=os.environ.copy();env.update(WINEPREFIX=str(R/'wineprefix'),WINEDEBUG='-all',AITALK_PRODUCT_NAME=product,AITALK_LICENSE_CODE=code)
 if style: env['TEST_STYLE']=style
 proc=subprocess.Popen(['wine',str(R/'src/daemon/build/voice_identity_probe.exe'),windows_path(EDITOR/'aitalk_engine.dll'),windows_path(license_path),windows_path(EDITOR/'Lang/standard/standard.aildic')],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log)
 def reply():
  b=proc.stdout.read(8)
  if len(b)!=8:raise RuntimeError(b)
  return struct.unpack('<iI',b)
 print('ready',label,reply(),flush=True)
 for name in ['KotonohaAkane_ns_48','KotonohaAoi_ns_48']:
  folder=EDITOR/'Voice'/name;wav=out/(name+'-'+label+'.wav')
  fields=['こんにちは。今日はいい天気ですね。',name,windows_path(folder/(name+'.aivdic')),windows_path(folder/'voice.lic'),windows_path(wav)]
  data=[f.encode() for f in fields];proc.stdin.write(struct.pack('<5I',*[len(f) for f in data])+b''.join(data));proc.stdin.flush()
  status=reply();print(label,name,status,hashlib.sha256(wav.read_bytes()).hexdigest()[:16] if wav.exists() else None,flush=True)
 proc.stdin.close();proc.wait(timeout=15);log.close()
 print((out/('probe-'+label+'.log')).read_text(errors='replace'),flush=True)
