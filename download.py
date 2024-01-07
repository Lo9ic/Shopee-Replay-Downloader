import requests
import subprocess
import os
from tqdm import tqdm

def clear_ts_files(directory):
    for filename in os.listdir(directory):
        if filename.endswith('.ts'):
            file_path = os.path.join(directory, filename)
            os.remove(file_path)

def get_m3u8_url(id):
    replay_api_url = f'https://live.shopee.co.id/api/v1/replay/{id}'
    response = requests.get(replay_api_url)
    data = response.json()
    
    if data.get('err_code') != 0:
        print(f"Failed to retrieve replay information for ID: {id}")
        return None

    replay_info = data.get('data', {}).get('replay_info', {})
    return replay_info.get('record_url', '')

def download_m3u8(id, output_dir='downloads', output_file='output.mp4'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    clear_ts_files(output_dir)

    m3u8_url = get_m3u8_url(id)
    if not m3u8_url:
        return

    m3u8_content = requests.get(m3u8_url).text
    lines = m3u8_content.split('\n')

    media_lines = [line for line in lines if line.endswith('.ts')]

    user_input_output_file = input("Enter the output file name (including extension, e.g., output.mp4): ")
    output_file = user_input_output_file if user_input_output_file else 'output.mp4'

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

# Example usage
user_input_id = input("Enter the replay ID: ")
download_m3u8(user_input_id)
