"""Tolerant C function boundaries and dependency context."""
import re

def masked(source):
    pattern=r'/\*[\s\S]*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''
    return re.sub(pattern,lambda m:''.join('\n' if c=='\n' else ' ' for c in m.group()),source)

def functions(source):
    """Tolerant lexical boundaries; strings/comments cannot create fake braces."""
    clean=masked(source);depth=0;opening=None;result=[]
    for i,char in enumerate(clean):
        if char=='{':
            if depth==0:opening=i
            depth+=1
        elif char=='}':
            depth-=1
            if depth<0:raise ValueError('Unbalanced closing brace')
            if depth==0:
                prefix=clean[:opening]
                m=re.search(r'(?m)^[ \t]*[\w* \t]+?\b([A-Za-z_]\w*)\s*\([^;{}]*\)\s*\Z',prefix)
                if m:
                    start=m.start();signature=source[start:opening].strip()
                    result.append({'name':m.group(1),'start':start,'body':opening,'end':i+1,
                                   'signature':signature,'text':source[start:i+1]})
    if depth:raise ValueError('Unbalanced braces: structural recovery required')
    if not result:raise ValueError('No C functions located')
    return result

def topology(source):
    fs=functions(source);names={f['name'] for f in fs}
    for f in fs:
        f['calls']=sorted((set(re.findall(r'\b([A-Za-z_]\w*)\s*\(',masked(source[f['body']+1:f['end']-1])))&names)-{f['name']})
    return fs

def context(source,names):
    fs=topology(source);parts=[];last=0
    for f in fs:
        parts.append(source[last:f['start']]);last=f['end']
    parts.append(source[last:])
    declarations=''.join(parts)
    interfaces='\n'.join(f['signature']+'; /* calls: '+','.join(f['calls'])+' */' for f in fs if f['name'] not in names)
    chunk='\n\n'.join(f['text'] for f in fs if f['name'] in names)
    return declarations,interfaces,chunk

def c_tokens(text):
    pattern=r'/\*[\s\S]*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[A-Za-z_]\w*|\d+(?:\.\d+)?|>>=|<<=|->|\+\+|--|<=|>=|==|!=|&&|\|\||[+*/%&|^<>=!-]=|<<|>>|[^\s]'
    return [(m.group(),m.start(),m.end()) for m in re.finditer(pattern,text)
            if not m.group().startswith(('/*','//'))]
