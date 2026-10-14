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
 # Source and rendered-view bounds must remain separate.
 large=Image.new('RGBA',(65,65),(20,40,60,255));buf=io.BytesIO();large.save(buf,format='PNG')
 for view in reviewer.neutral_views(buf.getvalue()):
  try:reviewer.png_dimensions(view)
  except reviewer.ReviewError:pass
  else:raise AssertionError('source dimension guard widened')
  assert reviewer.png_dimensions(view,rendered=True)==(520,520)
 print(json.dumps({'source_pixels_checked_per_background':256,'block_size':[8,8],'attachments':[128,128],'large_rendered_view':[520,520],'real_provider_calls':0}))
if __name__=='__main__':check()
