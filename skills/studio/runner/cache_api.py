"""Trusted native Messages conversion and dated cache accounting; no I/O."""
import base64
import copy
import json

FIELDS = ('prompt_tokens','completion_tokens','total_tokens','uncached_input_tokens',
          'cache_creation_input_tokens','cache_read_input_tokens',
          'cache_creation_5m_input_tokens','cache_creation_1h_input_tokens')
RATES_DATE = '2026-10-14'
# USD/MTok: uncached, 5m creation, 1h creation, read, output.
RATES = {'claude-sonnet-4-5-20250929': (3,3.75,6,.30,15),
         'claude-opus-5-5': (4,5,8,.20,20)}


def integer(value):
    if type(value) is not int or value < 0:
        raise ValueError('invalid token counter')
    return value


def native_usage(value):
    if not isinstance(value,dict): raise ValueError('native usage missing')
    plain=integer(value.get('input_tokens')); output=integer(value.get('output_tokens'))
    write=integer(value.get('cache_creation_input_tokens',0)); read=integer(value.get('cache_read_input_tokens',0))
    split=value.get('cache_creation',{'ephemeral_5m_input_tokens':write,'ephemeral_1h_input_tokens':0})
    if not isinstance(split,dict): raise ValueError('invalid cache creation split')
    five=integer(split.get('ephemeral_5m_input_tokens',0)); hour=integer(split.get('ephemeral_1h_input_tokens',0))
    if five+hour != write: raise ValueError('cache creation split disagrees')
    prompt=plain+write+read
    return dict(zip(FIELDS,(prompt,output,prompt+output,plain,write,read,five,hour)))


def usage(value):
    if not isinstance(value,dict): raise ValueError('token usage missing')
    prompt=integer(value.get('prompt_tokens')); output=integer(value.get('completion_tokens'))
    total=integer(value.get('total_tokens'))
    write=integer(value.get('cache_creation_input_tokens',0)); read=integer(value.get('cache_read_input_tokens',0))
    plain=integer(value.get('uncached_input_tokens',prompt-write-read))
    five=integer(value.get('cache_creation_5m_input_tokens',write)); hour=integer(value.get('cache_creation_1h_input_tokens',0))
    if total!=prompt+output or plain+write+read!=prompt or five+hour!=write:
        raise ValueError('token categories disagree')
    return dict(zip(FIELDS,(prompt,output,total,plain,write,read,five,hour)))


def estimate_cost(value,model):
    rates=RATES.get(model)
    if not rates: return None
    u=usage(value)
    counters=(u['uncached_input_tokens'],u['cache_creation_5m_input_tokens'],u['cache_creation_1h_input_tokens'],u['cache_read_input_tokens'],u['completion_tokens'])
    return round(sum(c*r for c,r in zip(counters,rates))/1000000,12)


def receipt(value,model):
    if not value: return {}
    result=usage(value)
    result['estimated_cost_usd']=estimate_cost(value,model)
    result['rates_date']=RATES_DATE if model in RATES else None
    return result


def blocks(content):
    if content is None: return []
    if isinstance(content,str): return [{'type':'text','text':content}] if content else []
    if not isinstance(content,list): raise ValueError('invalid message content')
    result=[]
    for item in content:
        if not isinstance(item,dict): raise ValueError('invalid content block')
        if item.get('type')=='text' and isinstance(item.get('text'),str):
            result.append({'type':'text','text':item['text']})
        elif item.get('type')=='image_url':
            url=item.get('image_url',{}).get('url','')
            if not isinstance(url,str) or not url.startswith(('data:image/png;base64,','data:image/jpeg;base64,')):
                raise ValueError('only inline PNG/JPEG images supported')
            prefix,data=url.split(',',1); decoded=base64.b64decode(data,validate=True)
            if len(decoded)>512*1024: raise ValueError('image exceeds limit')
            result.append({'type':'image','source':{'type':'base64','media_type':prefix[5:].split(';')[0],'data':data}})
        else: raise ValueError('unsupported message block')
    return result


def native_blocks(value):
    if not isinstance(value,list): raise ValueError('invalid native content')
    for b in value:
        if not isinstance(b,dict): raise ValueError('invalid native block')
        if 'cache_control' in b: raise ValueError('writer native cache marker refused')
        kind=b.get('type')
        if kind=='text':
            if not isinstance(b.get('text'),str): raise ValueError('invalid native text')
        elif kind=='thinking':
            if not isinstance(b.get('thinking'),str) or not isinstance(b.get('signature'),str): raise ValueError('invalid signed thinking')
        elif kind=='redacted_thinking':
            if not isinstance(b.get('data'),str): raise ValueError('invalid redacted thinking')
        elif kind=='tool_use':
            if (not isinstance(b.get('id'),str) or b.get('name') not in ('shell','view_image') or not isinstance(b.get('input'),dict)):
                raise ValueError('invalid native tool')
        else: raise ValueError('unsupported native block')
    return copy.deepcopy(value)


def native_request(request,prefix,max_tokens=32768):
    messages=request.get('messages')
    if not isinstance(messages,list) or not messages or messages[0]!={'role':'system','content':prefix['system']}:
        raise ValueError('operator prefix changed')
    if prefix.get('brief') is not None and (len(messages)<2 or messages[1]!={'role':'user','content':prefix['brief']}):
        raise ValueError('operator brief changed')
    system=blocks(prefix['system'])
    if not system: raise ValueError('empty operator system')
    system[-1]['cache_control']={'type':'ephemeral'}
    converted=[]
    for index,m in enumerate(messages[1:],1):
        if not isinstance(m,dict): raise ValueError('invalid native message')
        role=m.get('role')
        if role=='tool':
            if not isinstance(m.get('tool_call_id'),str) or not isinstance(m.get('content'),str):
                raise ValueError('invalid tool result')
            role='user'; content=[{'type':'tool_result','tool_use_id':m['tool_call_id'],'content':m['content']}]
        elif role in ('assistant','user'):
            if role=='assistant' and '_native_content' in m:
                content=native_blocks(m['_native_content'])
            else:
                content=blocks(m.get('content'))
                if role=='assistant':
                    for tool in m.get('tool_calls',[]):
                        f=tool['function']; content.append({'type':'tool_use','id':tool['id'],'name':f['name'],'input':json.loads(f['arguments'])})
                    native_blocks(content)
        else: raise ValueError('unsupported native message role')
        if index==1 and prefix.get('brief') is not None:
            if not content: raise ValueError('empty operator brief')
            content[-1]['cache_control']={'type':'ephemeral'}
        if converted and converted[-1]['role']==role: converted[-1]['content'].extend(content)
        else: converted.append({'role':role,'content':content})
    value={'model':request['model'],'max_tokens':max_tokens,'stream':False,'system':system,'messages':converted}
    if request.get('tools'):
        value['tools']=[{'name':t['function']['name'],'description':t['function']['description'],'input_schema':t['function']['parameters']} for t in request['tools']]
    # No automatic/growing breakpoint; writer-authored turns never carry markers.
    # Sampling fields are omitted: newer pinned models reject temperature=0.
    return value


def native_response(value,model):
    if not isinstance(value,dict): raise ValueError('invalid native response')
    counters=native_usage(value.get('usage'))
    message={'role':'assistant','content':''}; error=None
    try:
        if value.get('model')!=model or value.get('role')!='assistant': raise ValueError('native model or role mismatch')
        content=native_blocks(value.get('content'))
        message['_native_content']=content
        message['content']=''.join(b['text'] for b in content if b['type']=='text')
        calls=[{'id':b['id'],'type':'function','function':{'name':b['name'],'arguments':json.dumps(b['input'])}} for b in content if b['type']=='tool_use']
        if calls: message['tool_calls']=calls
        reason={'end_turn':'stop','stop_sequence':'stop','tool_use':'tool_calls','max_tokens':'length'}.get(value.get('stop_reason'))
        if not reason or (reason=='tool_calls')!=bool(calls): raise ValueError('invalid native stop reason')
    except (ValueError,TypeError,KeyError) as e:
        # Preserve validated paid usage even when the output cannot be used.
        reason='error'; error=str(e)
    result={'model':value.get('model'),'choices':[{'finish_reason':reason,'message':message}],'usage':counters}
    if error: result['_native_error']=error
    return result
