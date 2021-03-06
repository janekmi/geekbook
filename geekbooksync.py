#!/usr/bin/env python3
"""Push/pull a geekbook note to VM as readme and commit.

Usage::

    $ cat npdock.conf
    [Profile]
    RemoteFile = rpdock-vm:/home/rpdock/web/README.md
    # where git repository sits
    RemoteDir = /home/rpdock/web/
    LocalFile = notes/npdock-readme.md
    LocalTmpFile = npdock-readme.md.remote
    DiffTool = open -a diffmerge
    HeaderToStop = '# Misc' % # this can be used to break the coping, after this tag all informations stays on your computer
                              # test first with --dry --verbose to make sure that you are not going to push
                              # your private notes

push (works with images)::

    ./geekbook-sync.py --push npdock.conf
    # NPDock

    **NPDock** (Nucleic acid-Protein Dock) is a web server for modeling of RNA-protein and DNA-protein complex structures.
    It combines (1) GRAMM for global macromolecular docking, (2) scoring with a statistical potential, (3) clustering of best-scored structures, and (4) local refinement.

pull::

    ./geekbook-sync.py --pull npdock.conf
    scp rpdock-vm:/home/rpdock/web/README.md npdock-readme.md.remote
    README.md

if no change, no push will be made.

    npdock-readme.md.tosync                                                                                            100% 481     1.4MB/s   00:00
    On branch master
    Your branch is up-to-date with 'origin/master'.
    Changes not staged for commit:
        modified:   db.sqlite3

    Untracked files:
        .tramp_history

    no changes added to commit

required

- https://github.com/ekalinin/github-markdown-toc.go
- https://docs.python.org/3/library/configparser.html
"""  # noqa

import subprocess
import argparse
import os
import re
# import sys
# sys.path.append('/usr/local/lib/python3.6/site-packages/')
import configparser


def get_parser():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('profile_file', help='profile_file')
    parser.add_argument('--pull', help='push to the server', action='store_true')
    parser.add_argument('--push', help='push to the server', action='store_true')
    parser.add_argument('-d', '--dry', help="""dry, it sends files but doesn't push at the server
                        to git repository (so you can commit on your own""",
                        action='store_true')
    parser.add_argument('-v', '--verbose', help='push to the server', action='store_true')
    return parser


def get_file(fn, header_to_stop, verbose):
    def get_imgs(f):
        """e.g. imgs/Screen_Shot_2017-07-07_at_7.57.34_PM.png"""
        imgs = []
        for l in open(f):
            hit = re.search('\!\[.*?\]\((?P<path>.+)\)', l)
            if hit:
                imgs.append(hit.group('path'))
        return imgs

    def get_toc(f, verbose):
        cmd = "gh-md-toc " + f
        if verbose:
            print('gh-md-toc:', cmd)
        o = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = o.stdout.read().strip()
        return out.decode('utf-8')

    txt = open(fn).read()
    if header_to_stop:
        ntxt = ''
        for l in txt.split('\n'):
            if l.startswith(header_to_stop.replace("'", '')):
                print("break!")
                break
            ntxt += l + '\n'
    else:
        ntxt = txt

    tmpfile = 'sync_tmp.md'
    with open(tmpfile, 'w') as f:
        f.write(ntxt)

    imgs = get_imgs(tmpfile)

    toc = get_toc(tmpfile, verbose)
    txt = open(tmpfile).read()
    txt = txt.replace('[table_of_content]', toc)

    outf = '/tmp/' + os.path.basename(fn) + '.tosync'
    f = open(outf, 'w')
    f.write(txt)
    f.close()
    if verbose:
        print(txt)
    return imgs, outf


def fetch(remote_file, local_tmp_file, local_file, diff_tool):
    cmd = 'scp %s %s' % (remote_file, local_tmp_file)
    print(cmd)
    os.system(cmd)
    with open(local_tmp_file) as f:
        txt = f.read()

    ntxt = re.sub('Table of Contents.+markdown-toc.go\)', '[tableofcontent]', txt, flags=re.S)
    with open(local_tmp_file, 'w') as f:
        f.write(ntxt)

    cmd = 'diff ' + local_tmp_file + ' ' + local_file
    o = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if o.stdout.read().strip():  # if diff empty, file are the same
        cmd = diff_tool + ' ' + local_tmp_file + ' ' + local_file
        o = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        o.communicate()
        o.wait()
    else:
        print('The files are the same')


# main
if __name__ == '__main__':
    parser = get_parser()
    args = parser.parse_args()

    # load cfg
    cfg = configparser.ConfigParser()
    cfg.read(args.profile_file)
    remote_file = cfg.get('Profile', 'RemoteFile')
    local_tmp_file = cfg.get('Profile', 'LocalTmpFile')
    local_file = cfg.get('Profile', 'LocalFile')
    diff_tool = cfg.get('Profile', 'DiffTool')
    remote_dir = cfg.get('Profile', 'RemoteDir')
    try:
        header_to_stop = cfg.get('Profile', 'HeaderToStop')
    except configparser.NoOptionError:
        header_to_stop = None

    v = args.verbose

    if args.pull:
        fetch(remote_file, local_tmp_file, local_file, diff_tool)
    if args.push:
        imgs, outf = get_file(local_file, header_to_stop, args.verbose)
        if imgs:
            cmd = "ssh " + remote_file.split(':')[0] + " 'mkdir " + remote_dir + "/imgs/'"
            if v:
                print(cmd)
            os.system(cmd)
            for i in imgs:
                cmd = 'scp %s %s ' % (os.path.dirname(local_file) + os.sep + i,
                                      remote_file.split(':')[0] + ':' + remote_dir + i)
                if v:
                    print(cmd)
                os.system(cmd)

        cmd = 'scp %s %s ' % (outf, remote_file)
        print(cmd)
        os.system(cmd)

        cmd = "ssh " + remote_file.split(':')[0] + " 'cd " + \
              remote_dir + " ; git add imgs/* ; git add " + remote_file.split(
            '/')[-1] + " ; git -c color.status=always status " + \
            "; git commit -m \"readme update\" ; git push'"
        print(cmd)
        if not args.dry:
            os.system(cmd)

        if args.dry:
            print("\n!!!!!!!! DRY RUN don't pushed !!!!!!!!")
