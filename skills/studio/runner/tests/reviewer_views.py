#!/usr/bin/env python3
"""Pixel-exact view enlargement fixtures; trusted local PNGs, no model calls."""
import base64,io,json,sys
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import reviewer

def check():
 pixels=[((x*17)%256,(y*17)%256,((x+y)*11)%256,0 if (x+y)%5==0 else 255) for y in range(16) for x in range(16)]
 source=Image.new('RGBA',(16,16));source.putdata(pixels);buf=io.BytesIO();source.save(buf,format='PNG');data=buf.getvalue()
 views=reviewer.neutral_views(data)
 for view,bg in zip(views,(128,221)):
  image=Image.open(io.BytesIO(view)).convert('RGBA');assert image.size==(128,128),image.size
  for y in range(16):
   for x in range(16):
    r,g,b,a=pixels[y*16+x];expected=(r,g,b,255) if a else (bg,bg,bg,255)
    assert {image.getpixel((x*8+dx,y*8+dy)) for dx in range(8) for dy in range(8)}=={expected},(x,y,bg)
 attachments=reviewer.content(views)
 assert len(attachments)==2
 for a in attachments:
  payload=base64.b64decode(a['image_url']['url'].split(',',1)[1]);assert Image.open(io.BytesIO(payload)).size==(128,128)
 record=json.loads(reviewer.request_record([{'role':'user','content':attachments}]))
 assert all(a['image_url']['dimensions']==[128,128] for a in record[0]['content'])
 # Bounded factor keeps the existing 512px output cap.
 for size,factor in [(65,7),(256,2),(512,1)]:
  source=Image.new('RGBA',(size,size),(20,40,60,255));buf=io.BytesIO();source.save(buf,format='PNG')
  assert reviewer.view_metadata(buf.getvalue())=={'source_dimensions':[size,size],'scale':factor,'dimensions':[size*factor,size*factor]}
  assert all(reviewer.png_dimensions(v)==(size*factor,size*factor) for v in reviewer.neutral_views(buf.getvalue()))
 # Non-square, partial-alpha, one-pixel-wide shape; the native composite is
 # the oracle, independent of the resize implementation.
 source=Image.new('RGBA',(16,24),(0,0,0,0))
 for y in range(24):source.putpixel((7,y),(211,53,91,128 if y%2 else 255))
 buf=io.BytesIO();source.save(buf,format='PNG');data=buf.getvalue()
 import subprocess
 for view,bg in zip(reviewer.neutral_views(data),('#808080','#dddddd')):
  native=subprocess.check_output(['convert','png:-','-background',bg,'-alpha','remove','-alpha','off','-strip','PNG32:-'],input=data)
  expected=Image.open(io.BytesIO(native)).convert('RGBA').resize((128,192),Image.Resampling.NEAREST)
  actual=Image.open(io.BytesIO(view)).convert('RGBA');assert actual.size==(128,192)
  assert actual.tobytes()==expected.tobytes(),'non-square partial alpha or shape shifted'
 print(json.dumps({'source_pixels_checked_per_background':256,'block_size':[8,8],'attachments':[128,128],'non_square':[128,192],'partial_alpha_and_one_pixel_shape':True,'bounded_factors':{'65':7,'256':2,'512':1},'real_provider_calls':0}))
if __name__=='__main__':check()
