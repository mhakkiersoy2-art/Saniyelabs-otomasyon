#!/usr/bin/env python3
"""YouTube upload; requires owner's once-off OAuth consent. Never runs implicitly."""
import argparse,json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT=Path(__file__).resolve().parent
SCOPE=['https://www.googleapis.com/auth/youtube.upload']
AUTH=ROOT/'auth'

def youtube():
    token=AUTH/'youtube_token.json';client=AUTH/'client_secret.json'
    if not client.exists() and not token.exists():
        raise RuntimeError('YouTube OAuth client_secret.json dosyası gerekli. Google Cloud üzerinden kullanıcı onayı gerekir.')
    cred=None
    if token.exists():cred=Credentials.from_authorized_user_file(str(token),SCOPE)
    if not cred or not cred.valid:
        if cred and cred.expired and cred.refresh_token:cred.refresh(Request())
        else:
            if not client.exists():raise RuntimeError('Yeniden yetkilendirme için client_secret.json gerekli.')
            flow=InstalledAppFlow.from_client_secrets_file(str(client),SCOPE)
            cred=flow.run_local_server(port=0)
        token.write_text(cred.to_json(),encoding='utf8')
    return build('youtube','v3',credentials=cred)

def upload(file,meta,privacy):
    api=youtube()
    body={'snippet':{'title':meta['title'][:100], 'description':meta['description'], 'tags':meta['tags'], 'categoryId':'28'},
          'status':{'privacyStatus':privacy,'selfDeclaredMadeForKids':False}}
    job=api.videos().insert(part='snippet,status',body=body,media_body=MediaFileUpload(str(file),chunksize=-1,resumable=True,mimetype='video/mp4'))
    response=None
    while response is None: _,response=job.next_chunk()
    print('YouTube video ID:',response['id'])
    return response['id']

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('video')
    p.add_argument('--privacy',choices=['private','unlisted','public'],default='private')
    a=p.parse_args();file=Path(a.video)
    metadata=json.loads(file.with_suffix('.json').read_text(encoding='utf8'))
    print('Yükleniyor:',file.name,'gizlilik:',a.privacy)
    upload(file,metadata,a.privacy)
