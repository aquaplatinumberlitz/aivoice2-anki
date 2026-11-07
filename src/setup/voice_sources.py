"""Discover voice folders from the chosen source; import hashes record local data.

The stock MSI baseline constrains executable compatibility, not the list of
voicebanks a customer may supply. Publisher policy: Akane = Kansai, all other
voice families = standard (confirmed by the user on 2026-11-06).
"""
import hashlib
from pathlib import Path

LANGUAGES=('standard','kansai')
VOICE_LABELS={'KotonohaAkane_ns_48':'Akane (NV)','KotonohaAoi_ns_48':'Aoi (NV)',
              'MeikaHime_ns_48':'Meika Hime (NV)','MeikaMikoto_ns_48':'Meika Mikoto (NV)'}


def default_language(folder_name):
    return 'kansai' if 'akane' in folder_name.casefold() else 'standard'


def scan_voicebanks(source,registry):
    source=Path(source).expanduser()
    if not source.is_dir():return []
    found=[]
    for folder in sorted(source.iterdir()):
        if not folder.is_dir():continue
        issues=[]
        if folder.is_symlink():issues.append('Thư mục là symlink')
        packages=sorted(folder.glob('*.aivdic'))
        canonical=folder/(folder.name+'.aivdic')
        package=canonical if canonical in packages else (packages[0] if len(packages)==1 else None)
        if package is None:issues.append('Thiếu gói .aivdic hoặc có nhiều gói không rõ giọng chính')
        for name in ['voice.lic','images.dat']:
            if not (folder/name).is_file():issues.append('Thiếu '+name)
        if not any((folder/name).is_file() for name in ['info.bin','infox.bin']):
            issues.append('Thiếu info.bin/infox.bin cho GUI')
        if any(path.is_symlink() for path in folder.rglob('*')):issues.append('Có file/thư mục symlink')
        found.append({'folder':folder.name,'label':VOICE_LABELS.get(folder.name,folder.name),
                      'package':package.name if package else None,
                      'language':default_language(folder.name),
                      'issues':issues,'files_ready':not issues})
    return found


def inventory_tree(root,source_id,prefix=''):
    root=Path(root)
    if root.is_symlink():raise ValueError('Không import source là symlink')
    result=[]
    for path in sorted(root.rglob('*')):
        if path.is_symlink():raise ValueError(f'Source có symlink: {path.name}')
        if not path.is_file():continue
        with path.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
        relative=path.relative_to(root).as_posix()
        result.append({'source':source_id,'path':prefix+relative,'bytes':path.stat().st_size,'sha256':digest})
    return result


def prepare_voice_import(voicebanks,languages,selected,registry,dialects=None,installed_languages=None):
    selected=sorted(set(selected));dialects=dialects or {}
    if not selected:raise ValueError('Chọn ít nhất một giọng trong thư mục nguồn')
    discovered={item['folder']:item for item in scan_voicebanks(voicebanks,registry)}
    updated={name:dict(entry) for name,entry in registry.items()}
    voice_files=[];catalog={};needed={'standard'}
    for name in selected:
        item=discovered.get(name)
        if item is None:raise ValueError(f'Giọng không nằm trong thư mục đã chọn: {name}')
        if item['issues']:raise ValueError(name+': '+', '.join(item['issues']))
        language=dialects.get(name,item['language'])
        if language not in LANGUAGES:
            raise ValueError(f'{name}: chưa xác định dialect. Chọn Standard hoặc Kansai cho giọng này.')
        updated[name]={**updated.get(name,{}),'language':language,'distribution':'user-selected-source',
                       'evidence':'voice-imports.json#'+name,
                       'dialect_basis':'explicit-override' if language!=default_language(name) else 'publisher-policy-akane-kansai-others-standard'}
        needed.add(language)
        files=inventory_tree(Path(voicebanks)/name,'selected-voicebanks',prefix=name+'/')
        voice_files.extend(files)
        catalog[name]={'language':language,'package':item['package'],'files':files}
    lang_files=[]
    for language in sorted(needed):
        folder=Path(languages)/language
        if not (folder/(language+'.aildic')).is_file():
            if installed_languages and (Path(installed_languages)/language/(language+'.aildic')).is_file():
                continue
            raise ValueError('Thiếu Lang/'+language+'/'+language+'.aildic trong nguồn đã chọn')
        lang_files.extend(inventory_tree(folder,'selected-language',prefix=language+'/'))
    return voice_files,lang_files,updated,catalog


def parse_dialects(values):
    result={}
    for value in values or []:
        name,separator,language=value.partition('=')
        if not separator or not name or language not in LANGUAGES:
            raise ValueError('--dialect cần dạng tên-thư-mục=standard hoặc tên-thư-mục=kansai')
        result[name]=language
    return result
