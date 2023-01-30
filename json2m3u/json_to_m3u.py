from typing import NoReturn

def get_category_name(id, categories) -> str:
    """
    :id: Category ID.
    :categories: List of categories.
    :return: Category name.
    """
    for category in categories:
        if id == category.get('id'):
            return category.get('name', 'No Category')
    return 'No Category'


def generate_file(data, filename) -> NoReturn:
    """
    :data: JSON data.
    :filename: Output filename.
    This will probably not work with other providers without some changes. ¯\_(ツ)_/¯
    """
    default_user_agent = 'NSPlayer/9.0.0.3268' # User-Agent expected by the provider.
    with open(f'{filename}.m3u', 'w') as out_file:
        out_file.write('#EXTM3U\n')
        sorted_list = data['channel_info']
        sorted_list = sorted(sorted_list, key=lambda k: k['name'])
        for channel in sorted_list:
            tvg_name = channel.get('epg_id')
            tvg_logo = channel.get('icon')
            channel_name = channel.get('name')
            category_name = get_category_name(channel.get('category_id'), data['category_info'])
            url = channel.get('url')
            out_file.write(f'#EXTINF:-1 tvg-name="{tvg_name}" tvg-logo="{tvg_logo}", {channel_name}\n')
            out_file.write(f'#EXTGRP:{category_name}\n')
            out_file.write(f'#EXTVLCOPT:http-user-agent={default_user_agent}\n') 
            out_file.write(f'{url}\n')

def get_random_string() -> str:
    """
    :return: A random 8 chars long string.
    """
    import string
    import random
    return ''.join(random.choice(string.ascii_lowercase) for i in range(8))
    

def main(filename) -> NoReturn:
    import json
    from urllib.request import urlopen # Used instead of 'requests' to keep it self-contained.
    prev_filename = None
    cur_filename = f'{get_random_string()}'
    try:
        with open(filename, 'r') as in_file:
            while (line := in_file.readline().rstrip()):
                if line.startswith('#'):
                    # Comment, therefore skipping.
                    continue
                elif line.startswith(';'):
                    # Output filename, update string
                    prev_filename = cur_filename
                    cur_filename = line[1:]
                else:
                    result = urlopen(line)
                    try:
                        data = json.loads(result.read())
                        if prev_filename == cur_filename:
                            # Avoid duplicate filename
                            cur_filename = get_random_string()
                        generate_file(data, cur_filename)
                    except json.JSONDecodeError:
                        print(f"{line} didn't return parseable JSON content, skipping...")
                        continue
    except FileNotFoundError:
        print('File does not exist. Please verify your path.')

if __name__ == '__main__':
    import argparse
    description = "Generate a M3U8 playlist from JSON"
    epilog = "Filespec: Lines are treated as a URL. Comments are prepended with a '#'. To specific a output filename for the URL, insert a line above the URL prepended with a ';', you don't need to specify the extension. If you don't specify a filename, a random one will be generated."
    parser = argparse.ArgumentParser(description=description, epilog=epilog)
    parser.add_argument('filename', help='Path to the file. See filespec for details.')
    args = parser.parse_args()
    main(args.filename)