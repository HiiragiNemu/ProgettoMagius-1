"""Exact scalar-value changes in reviewed scenario JSON, with path/baseline checks."""
import json
import hashlib

def blob(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()

def spans(raw):
    text=raw.decode('utf-8-sig');decoder=json.JSONDecoder();result={};size=len(text)
    def skip(i):
        while i<size and text[i] in ' \t\r\n':i+=1
        return i
    def walk(i,path):
        i=skip(i)
        if text[i]=='{':
            i=skip(i+1);seen=set()
            if text[i]=='}':return i+1
            while True:
                key,j=decoder.raw_decode(text,i)
                if not isinstance(key,str) or key in seen:raise ValueError('Invalid or duplicate key')
                seen.add(key);j=skip(j);assert text[j]==':'
                i=skip(walk(j+1,path+(key,)))
                if text[i]=='}':return i+1
                assert text[i]==',';i=skip(i+1)
        if text[i]=='[':
            i=skip(i+1);index=0
            if text[i]==']':return i+1
            while True:
                i=skip(walk(i,path+(index,)));index+=1
                if text[i]==']':return i+1
                assert text[i]==',';i=skip(i+1)
        value,j=decoder.raw_decode(text,i);result[path]=(i,j,value);return j
    assert skip(walk(0,()))==size
    return text,result

def apply(raw,operations):
    text,positions=spans(raw);edits=[];seen=set();original=json.loads(raw)
    for address,before,after in operations:
        key=tuple(address)
        if key not in positions or key in seen:raise ValueError('Missing or duplicate edit path')
        start,end,current=positions[key];seen.add(key)
        if current!=before or type(current)!=type(before) or before==after:raise ValueError('Baseline mismatch')
        edits.append((start,end,json.dumps(after,ensure_ascii=False,allow_nan=False)))
    result=text
    for start,end,value in sorted(edits,reverse=True):result=result[:start]+value+result[end:]
    prefix=b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b''
    candidate=prefix+result.encode();restored=json.loads(candidate)
    for address,before,after in operations:
        node=restored
        for key in address[:-1]:node=node[key]
        assert node[address[-1]]==after;node[address[-1]]=before
    assert restored==original
    return candidate
