#!/usr/bin/env python3

import os
import re
import sys
import time
import string
import pathlib
import argparse
import subprocess

VIDEOS_EXT = '.mp4'
CODEC = 'libx265'
RATE = 26
ORIGINALS_FOLDER = '_orig/'
PROCESSED_SUFFIX = 'min'
GREATER_THAN = '4M'

def _human_to_byte(size):
    size_name = {'K':1, 'M':2, 'G':3}
    for s in size_name:
        if size.endswith(s):
            num = int(size[:-1])
            idx = size_name[s]
            factor = 1024 ** idx
            return num * factor
    raise ValueError(size)

def _byte_to_human(num):
    for unit in ['', 'K', 'M', 'G']:
        if abs(num) < 1024.0:
            return f'{num:3.1f}{unit}'
        num /= 1024.0
    return f'{num:.1f}Yi'

class HumanReadableSizeType(object):
    def __call__(self, string):
        return _human_to_byte(string)

def _prepare_processing(args, folder):
    print(f'\nProcessing folder: {folder}')
    
    ends_with = lambda f, ext: f.lower().endswith(ext.lower())

    file_paths = [os.path.join(folder, f) for f in os.listdir(folder)]
    files = [f for f in file_paths if os.path.isfile(f) \
        and ends_with(f, args.video_files)]
    print(f'\tFound {len(files)} video files ({args.video_files})')

    result = []
    for f in files:
        processed_mask = f'{args.suffix}{args.video_files}'
        if not args.overwrite_processed and ends_with(f, processed_mask):
            print(f'\tSkipping {f} since it is already processed.')
        else:
            size = os.path.getsize(f)
            if size < args.greater_than:
                print(f'\tSkipping {f}({_byte_to_human(size)}) since it is smaller than {_byte_to_human(args.greater_than)}.')
            else:
                result.append(f)
    if not result:
        print(f'\n\tLooks like there is nothing to do in folder {folder}\n')
        return None

    print(f'\n\tProceeding to process {len(result)} files:')
    print('\t' + '\n\t'.join(result))

    if args.originals == 'move':
        orig_folder = os.path.join(folder, args.originals_folder)
        try:
            os.mkdir(orig_folder)
            print(f'\n\tCreated subfolder for original files: {orig_folder}')
        except FileExistsError:
            print(f'\n\tSubfolder for original files already exists: {orig_folder}')

    return result

def _process_file(args, folder, file, index, count):
    stat = lambda: None
    stat.original = file

    size = os.path.getsize(file)
    stat.original_size = size

    print (f'\n\t[{index+1}/{count}] Processing {file} ({_byte_to_human(size)})')
    start_time = time.time()

    command = ['ffmpeg', '-y',  # Base command
        '-i', file,             # Input
        '-vcodec', args.codec,  # Codec
        '-crf', str(args.rate)] # Compression rate
    # Output file
    filename = pathlib.Path(file).stem
    output_file = os.path.join(folder, f'{filename}.{args.suffix}{args.output_video_files}')
    stat.output_file = output_file
    command.append(f'{output_file}')
    # Additional
    if not args.skip_ffmpeg_report:
        command.append('-report')

    print (f'\t\tRunning ffmpeg to create {output_file}')
    # ffmpeg -i "$fullpath" -vcodec libx265 -crf 26 "$newpath"
    subprocess.run(command, stdout = subprocess.DEVNULL, stderr = subprocess.STDOUT)    

    # original file post processing
    if args.originals == 'move':
        destination = os.path.join(folder, args.originals_folder, os.path.basename(file))
        print(f'\t\tMoving original file to {destination}.')
        os.rename(file, destination)
        stat.original_moved = destination
    elif args.originals == 'delete':
        print(f'\t\tDeleting original file.')
        os.remove(file)

    elapsed = time.time() - start_time
    stat.elapsed = elapsed
    print (f'\t\tDONE ({elapsed:.2f}s)')

    return stat

def _run_processing(args, folder, files):
    stats = []
    i = 0
    for f in files:
        s = _process_file(args, folder, f, i, len(files))
        stats.append(s)
        i += 1
    return stats

def _display_stats(stats):
    print()

def main():
    parser = argparse.ArgumentParser(description='Process video files with ffmpeg',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('FOLDERS', nargs='+', help = 'Process videos in these folders.')
    parser.add_argument('-v', '--video-files', default = VIDEOS_EXT,
        help = 'Process videos with this extension.')
    parser.add_argument('-g', '--greater-than', default=GREATER_THAN, type=HumanReadableSizeType(),
        help='Process only files greater than this. Value shoult be int number with size suffix (K, M, G).')
    parser.add_argument('-w', '--overwrite-processed', default = False, action = 'store_true',
        help = 'Overwrite previously processed videos (detect by suffix) and process them again.')
    parser.add_argument('-s', '--suffix', default=PROCESSED_SUFFIX,
        help='Suffix to add to the name of processed files.')
    parser.add_argument('-x', '--output-video-files', default=VIDEOS_EXT,
        help='Extension of processed video files.')
    parser.add_argument('-c', '--codec', default=CODEC, help='Codec to use for processing.')
    parser.add_argument('-r', '--rate', default=RATE, type=int, help='Processing compression rate.')
    parser.add_argument('-o', '--originals', choices=['leave', 'move', 'delete'],
        default = 'move', help='How to handle original files after processing.')
    parser.add_argument('-f', '--originals-folder', default=ORIGINALS_FOLDER, help='Subfolder to save originals into.')
    
    parser.add_argument('--skip-ffmpeg-report', default = False, action = 'store_true',
        help='Do not write ffmpeg report with extended conversion information')

    args = parser.parse_args()
    print(f'Starting processing with these parameters:\n{args}')

    for folder in args.FOLDERS:
        files = _prepare_processing(args, folder)
        if files:
            stats = _run_processing(args, folder, files)
            _display_stats(stats)

    print('\nFinished.\n')

if __name__ == '__main__':
    main()
