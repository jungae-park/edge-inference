import torch

torch.hub.download_url_to_file('https://ultralytics.com/assets/coco2017val.zip', 'tmp.zip')
unzip -q tmp.zip -d ../datasets && rm tmp.zip