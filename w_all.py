#!/usr/bin/env python3

import os
import re
import sys
import time
import string
import pathlib
import argparse
import subprocess
from datetime import timedelta

VIDEOS_EXT = '.mp4'
CODEC = 'libx265'
RATE = 26
ORIGINALS_FOLDER = '_orig/'
PROCESSED_SUFFIX = 'min'
GREATER_THAN = '30M'
ORIGINAL_HANDLING_OPTIONS = ('leave', 'move', 'delete')

class _print:
    level = 0

    def __filtered(s, lvl):
        if lvl >= _print.level:
            print(s)

    def totals(s):
        _print.__filtered(s, 4)

    def folder(s):
        _print.__filtered(s, 3)

    def file(s):
        _print.__filtered('\t' + s, 2)

    def filedetails(s):
        _print.__filtered('\t\t' + s, 1)

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

def _prepare_folder(args, folder, index, count):
    _print.folder(f'\n[{index+1}/{count}] Processing folder: {folder}')
    
    ends_with = lambda f, ext: f.lower().endswith(ext.lower())

    file_paths = [os.path.join(folder, f) for f in os.listdir(folder)]
    files = [f for f in file_paths if os.path.isfile(f) \
        and ends_with(f, args.video_files)]
    _print.folder(f'\tFound {len(files)} video files ({args.video_files})')

    result = []
    skipped = 0
    for f in files:
        processed_mask = f'{args.suffix}{args.video_files}'
        if not args.overwrite_processed and ends_with(f, processed_mask):
            _print.filedetails(f'- Skipping {f} since it is already processed.')
            skipped +=1
        else:
            size = os.path.getsize(f)
            if size < args.greater_than:
                _print.filedetails(f'- Skipping {f}({_byte_to_human(size)}) since it is smaller than {_byte_to_human(args.greater_than)}.')
                skipped +=1
            else:
                result.append(f)
    if skipped > 0:
        _print.folder(f'\tSkipped {skipped} files.')

    if not result:
        _print.folder(f'\n\tLooks like there is nothing to do in folder {folder}.\n')
        return None

    _print.folder(f'\tProceeding to process {len(result)} files')
    for f in result:
        _print.filedetails('- ' + f)

    if args.originals == 'move':
        orig_folder = os.path.join(folder, args.originals_folder)
        try:
            os.mkdir(orig_folder)
            _print.folder(f'\n\tCreated subfolder for original files: {orig_folder}')
        except FileExistsError:
            _print.folder(f'\n\tSubfolder for original files already exists: {orig_folder}')

    return result

def _process_file(args, folder, file, index, count):
    stat = lambda: None
    stat.original = file

    size = os.path.getsize(file)
    stat.original_size = size

    _print.file('')
    _print.file(f'[{index+1}/{count}] Processing {file} ({_byte_to_human(size)})')
    start_time = time.time()

    command = ['ffmpeg', '-y',  # Base command
        '-i', file,             # Input
        '-vcodec', args.codec,  # Codec
        '-crf', str(args.rate)] # Compression rate
    
    # If recoding from other formats to mp4 add audio codec params
    if args.video_files != '.mp4':
         command += ['-c:a', 'aac', '-q:a', '100']
         _print.filedetails('Extended ffmpeg params with audio codec to handle conversion.')

    # Output file
    filename = pathlib.Path(file).stem
    output_file = os.path.join(folder, f'{filename}.{args.suffix}{args.output_video_files}')
    stat.output_file = output_file
    command.append(f'{output_file}')
    # Additional
    if args.ffmpeg_report:
        command.append('-report')

    _print.filedetails(f'Running ffmpeg to create {output_file}')
    # ffmpeg -i "$fullpath" -vcodec libx265 -crf 26 "$newpath"
    subprocess.run(command, stdout = subprocess.DEVNULL, stderr = subprocess.STDOUT)    
    stat.output_file_size = os.path.getsize(output_file)

    # original file post processing
    if args.originals == 'move':
        destination = os.path.join(folder, args.originals_folder, os.path.basename(file))
        _print.filedetails(f'Moving original file to {destination}.')
        os.rename(file, destination)
        stat.original_moved = destination
    elif args.originals == 'delete':
        _print.filedetails(f'Deleting original file.')
        os.remove(file)

    elapsed = time.time() - start_time
    stat.elapsed = elapsed
    stat.delta_size = size - stat.output_file_size
    stat.delta_percent = 100 * float(stat.output_file_size) / size
    _print.filedetails(f'New size: {_byte_to_human(stat.output_file_size)}, ({stat.delta_percent:.1f}% of original, saved {_byte_to_human(stat.delta_size)})')
    _print.file(f'\tDONE in {timedelta(seconds=int(elapsed))}')

    return stat

def _process_folder(args, folder, files):
    stats = []
    i = 0
    start_time = time.time()
    for f in files:
        s = _process_file(args, folder, f, i, len(files))
        stats.append(s)
        i += 1
    elapsed = time.time() - start_time
    return elapsed, stats

def _display_folder_stats(folder, elapsed, files_stats):
    _print.folder(f'\n\tTotals for {folder}')
    old_total_size = sum([stat.original_size for stat in files_stats])
    _print.folder(f'\tProcessed {len(files_stats)} files ({_byte_to_human(old_total_size)} in total) in {timedelta(seconds=int(elapsed))}')
    new_total_size = sum([stat.output_file_size for stat in files_stats])
    delta_size = old_total_size - new_total_size
    delta_percent = 100 * float(new_total_size) / old_total_size
    _print.folder(f'\tNew total size: {_byte_to_human(new_total_size)}, ({delta_percent:.1f}% of original, saved {_byte_to_human(delta_size)})\n')

def _display_total_stats(elapsed, folders_count, files_stats):
    if files_stats:
        old_total_size = sum([stat.original_size for stat in files_stats])
        _print.totals(f'Processed {len(files_stats)} files in {folders_count} folder(s) ({_byte_to_human(old_total_size)}  in total) in {timedelta(seconds=int(elapsed))}')
        new_total_size = sum([stat.output_file_size for stat in files_stats])
        delta_size = old_total_size - new_total_size
        delta_percent = 100 * float(new_total_size) / old_total_size
        _print.totals(f'New total size: {_byte_to_human(new_total_size)}, ({delta_percent:.1f}% of original, saved {_byte_to_human(delta_size)})\n')

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
    parser.add_argument('-o', '--originals', choices=ORIGINAL_HANDLING_OPTIONS,
        default = 'move', help='How to handle original files after processing.')
    parser.add_argument('-f', '--originals-folder', default=ORIGINALS_FOLDER, help='Subfolder to save originals into.')
    parser.add_argument('--display-verbosity', type=int, choices=range(1, 4),
        default = 2, help='Verbosity of processing progress display.')
    parser.add_argument('--ffmpeg-report', default = False, action = 'store_true',
        help='Write ffmpeg report with extended conversion information')

    args = parser.parse_args()
    _print.level = args.display_verbosity
    _print.totals(f'Starting processing with these parameters:\n{args}')

    i = 0
    start_time = time.time()
    total_stats = []
    for folder in args.FOLDERS:
        files = _prepare_folder(args, folder, i, len(args.FOLDERS))
        if files:
            elapsed, stats = _process_folder(args, folder, files)
            _display_folder_stats(folder, elapsed, stats)
            total_stats += stats
        i += 1
    elapsed = time.time() - start_time
    _display_total_stats(elapsed, len(args.FOLDERS), total_stats)

    _print.totals('FINISHED.\n')

if __name__ == '__main__':
    main()
