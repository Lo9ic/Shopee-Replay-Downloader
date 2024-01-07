import requests
import subprocess
import os
from tqdm import tqdm

def clear_ts_files(directory):
    for filename in os.listdir(directory):
        if filename.endswith('.ts'):
            file_path = os.path.join(directory, filename)
            os.remove(file_path)

def get_record_ids(session_id):
    replay_api_url = f'https://live.shopee.co.id/api/v1/replay?session_id={session_id}'
    response = requests.get(replay_api_url)
    data = response.json()
    
    if data.get('err_code') != 0:
        print(f"Failed to retrieve replay information for session ID: {session_id}")
        return None

    record_ids = data.get('data', {}).get('record_ids', [])
    return record_ids

def get_m3u8_url(record_id):
    replay_api_url = f'https://live.shopee.co.id/api/v1/replay/{record_id}'
    response = requests.get(replay_api_url)
    data = response.json()
    
    if data.get('err_code') != 0:
        print(f"Failed to retrieve replay information for record ID: {record_id}")
        return None

    replay_info = data.get('data', {}).get('replay_info', {})
    return replay_info.get('record_url', '')

def download_m3u8(record_id, output_dir='downloads', output_file='output.mp4'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    clear_ts_files(output_dir)

    m3u8_url = get_m3u8_url(record_id)
    if not m3u8_url:
        return

    m3u8_content = requests.get(m3u8_url).text
    lines = m3u8_content.split('\n')

    media_lines = [line for line in lines if line.endswith('.ts')]

    with tqdm(total=len(media_lines), desc='Downloading segments') as pbar:
        for index, media_line in enumerate(media_lines):
            media_url = m3u8_url.rsplit('/', 1)[0] + '/' + media_line
            segment_file = os.path.join(output_dir, f'segment_{index}.ts')
            with open(segment_file, 'wb') as f:
                f.write(requests.get(media_url).content)
            pbar.update(1)

    concat_file_path = os.path.join(output_dir, 'concat.txt')
    with open(concat_file_path, 'w') as f:
        for index in range(len(media_lines)):
            f.write(f"file 'segment_{index}.ts'\n")

    with tqdm(total=1, desc='Converting to MP4') as pbar:
        output_path = os.path.join(output_dir, output_file)
        subprocess.run(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', concat_file_path, '-c', 'copy', output_path])
        pbar.update(1)

    for index in range(len(media_lines)):
        os.remove(os.path.join(output_dir, f'segment_{index}.ts'))

    print(f'Conversion complete. Output saved to: {output_path}')

user_input_session_id = input("Enter the session ID: ")
record_ids = get_record_ids(user_input_session_id)

if record_ids:
    for record_id in record_ids:
        download_m3u8(record_id)
