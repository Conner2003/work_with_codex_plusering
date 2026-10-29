#!/usr/bin/env python3
"""Offline APK metadata and privacy-inventory helper. No code execution from APK."""
import re, zipfile, struct, collections, json, hashlib, sys
from pathlib import Path

apk=Path(sys.argv[1]) if len(sys.argv)>1 else Path('PulseRing Super V2.8.1.apk')
out=Path(sys.argv[2]) if len(sys.argv)>2 else Path('analysis')
out.mkdir(parents=True,exist_ok=True)

def uleb(b,p):
    x=0
    for k in range(5):
        v=b[p];p+=1;x |= (v&0x7f) << (7*k)
        if v<128:return x,p
    raise ValueError('Invalid uleb')

def dexinfo(b):
    if not b[:4]==b'dex\n': raise ValueError('Not DEX')
    u32=lambda p:struct.unpack_from('<I',b,p)[0]
    ssz,soff=u32(56),u32(60)
    strs=[]
    for i in range(ssz):
        off=u32(soff+i*4)
        _,pos=uleb(b,off)
        end=b.find(b'\0',pos)
        strs.append(b[pos:end].decode('utf-8','replace'))
    ntype,typeoff=u32(64),u32(68)
    types=[strs[u32(typeoff+i*4)] for i in range(ntype)]
    ncls,clsoff=u32(96),u32(100)
    descs=[]; cls_infos=[]
    for i in range(ncls):
        klass,flags,parent,ifc,src,ann,data,static=struct.unpack_from('<8I',b,clsoff+i*32)
        descriptor=types[klass]
        descs.append(descriptor)
        cls_infos.append({'name':descriptor,'access_flags':flags,'super':types[parent] if parent<ntype else None,'source':strs[src] if src<len(strs) else None})
    nmethods,moff=u32(88),u32(92)
    methodclasses=collections.Counter()
    for i in range(nmethods):
        cidx,proto,name=struct.unpack_from('<HHI',b,moff+i*8)
        if cidx<len(types):methodclasses[types[cidx]]+=1
    return {'string_count':ssz,'type_count':ntype,'class_count':ncls,'method_id_count':nmethods,'classes':cls_infos,'strings':strs,'methodcounts':methodclasses}

def axml_strings(b):
    if b[:4]!=b'\x03\x00\x08\x00':return []
    # StringPool chunk (0x0001); parse UTF8 or UTF16 strings.
    for off in range(8,min(len(b),0x2000),4):
        if off+28>len(b): break
        typ,hs,sz=struct.unpack_from('<HHI',b,off)
        if typ!=1 or not (hs>=28 and sz>hs and off+sz<=len(b)):continue
        count,sty,flags,start,styles=struct.unpack_from('<5I',b,off+8)
        if count>200000 or off+hs+count*4>off+sz:continue
        utf8=bool(flags&0x100)
        strs=[]
        def l8(p):
            c=b[p];p+=1
            if c&0x80:c=((c&0x7f)<<8)|b[p];p+=1
            return c,p
        def l16(p):
            c=struct.unpack_from('<H',b,p)[0];p+=2
            if c&0x8000:c=((c&0x7fff)<<16)|struct.unpack_from('<H',b,p)[0];p+=2
            return c,p
        for j in range(count):
            rel=struct.unpack_from('<I',b,off+hs+j*4)[0]
            p=off+start+rel
            if p>=off+sz: continue
            try:
                if utf8:
                    _,p=l8(p);size,p=l8(p);s=b[p:p+size].decode('utf-8','replace')
                else:
                    size,p=l16(p);s=b[p:p+size*2].decode('utf-16-le','replace')
                strs.append(s)
            except Exception:pass
        return strs
    return []

sha=hashlib.sha256(apk.read_bytes()).hexdigest()
dexes=[]
with zipfile.ZipFile(apk) as z:
    files=z.namelist()
    info={'filename':apk.name,'sha256':sha,'file_bytes':apk.stat().st_size,'zip_entries':len(files), 'dex':[],'native_libs':[x for x in files if x.endswith('.so')], 'assets':[x for x in files if x.startswith('assets/')], 'resource_file_count':sum(x.startswith('res/') for x in files)}
    manifest_strs=axml_strings(z.read('AndroidManifest.xml'))
    (out/'manifest-string-pool.txt').write_text('\n'.join(manifest_strs),encoding='utf-8')
    for name in files:
        if name.endswith('.dex'):
            d=dexinfo(z.read(name));dexes.append(d)
            info['dex'].append({'file':name,'classes':d['class_count'],'methods':d['method_id_count'],'strings':d['string_count']})
    appclasses=[]
    for i,d in enumerate(dexes):
        for cl in d['classes']:
            if cl['name'].startswith(('Lcom/conner/','Lcom/connor/')):
                appclasses.append({'dex':info['dex'][i]['file'],**cl,'method_id_count':d['methodcounts'][cl['name']]})
    (out/'application-class-inventory.json').write_text(json.dumps(appclasses,ensure_ascii=False,indent=2),encoding='utf-8')
    info['candidate_app_class_count']=len(appclasses)
    prefixes=collections.Counter()
    for d in dexes:
        for c in d['classes']:
            s=c['name']
            if s.startswith('L'):
                spl=s[1:].split('/')
                if len(spl)>2:prefixes['/'.join(spl[:min(3,len(spl)-1)])]+=1
    info['major_package_prefixes']=prefixes.most_common(35)
    # Potential safety flags with no value exfiltration and without exposing secrets.
    suspects=[]
    patterns=[('google_api_key',re.compile(r'^AIza[0-9A-Za-z_-]{30,}$')),('openai_api_key',re.compile(r'^sk-(?:proj-)?[a-zA-Z0-9_-]{18,}$')),('discord_bot_token',re.compile(r'^[A-Za-z0-9_-]{20,30}\.[A-Za-z0-9_-]{6,8}\.[A-Za-z0-9_-]{20,}$'))]
    for i,d in enumerate(dexes):
        for s in d['strings']:
            for label,pat in patterns:
                if pat.search(s):
                    suspects.append({'dex':info['dex'][i]['file'],'type':label,'redacted':'[REDACTED]','sha256_prefix':hashlib.sha256(s.encode()).hexdigest()[:12]})
    info['possible_secret_matches']=suspects
    info['manifest_relevant_strings']=[s for s in manifest_strs if any(t in s.lower() for t in ['com.conner','fixfate','puls','bluetooth','location','notification','foreground','android.permission','android.intent'])][:100]
    (out/'apk-metadata.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'apk_sha256':sha,'dex_count':len(dexes),'candidate_app_classes':len(appclasses),'total_classes':sum(d['class_count'] for d in dexes),'suspicious_literals':len(suspects),'top_packages':prefixes.most_common(12),'manifest_relevant':info['manifest_relevant_strings'][:30]},ensure_ascii=False,indent=2))
