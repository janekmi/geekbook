"""This is a set of functions that work on Markdown file, before compiling them to html."""

from engine.conf import PATH_TO_IMG
import re
import os

import logging
logger = logging.getLogger('geekbook')
logger.setLevel(logging.INFO)

def change_todo_square_chainbox_or_icon(text, verbose=False):
    """Set of rules to replace [i] etc with <img ... >  [ OK ]"""
    ## of list
    text = text.replace('<li>[ ]', '<li><input type="checkbox" />')
    text = text.replace('<li>[X]', '<li><input type="checkbox" checked="checked" />')
    ## every [ ] is change
    text = text.replace('[ ]','<input type="checkbox" />')
    text = text.replace('[X]','<input type="checkbox" checked="checked" />')
    return text


def get_todo(text):
    ntext = ''
    for l in text.split('\n'):
        if not l.startswith('#'):
            l = l.replace('@todo', '<span class="label label-danger">@todo</span>')
        ntext += l + '\n'
    ntext = change_todo_square_chainbox_or_icon(ntext)
    return ntext

def get_abstract(text):
    ntext = ''
    for l in text.split('\n'):
        if l.startswith('|'):
            l = '<div class="abstract"> ' + l[1:] + '</div>'
        ntext += l + '\n'
    return ntext


def get_image_path(text):
    """Get image path for l(ine)."""

    def get_image_path(l):
        """Get image path for l(ine).

        :rtype: string, line
        """
        rx = re.compile('\!\[\]\((?P<filename>.+)\)').search(l)

        if rx:
            path_new = '<a class="lightbox" href="' + PATH_TO_IMG + '/' + rx.group('filename') +'">'+\
                       '<img src="' + PATH_TO_IMG + '/' + rx.group('filename') + \
                       '" alt="" title=""></a> \n'
            return path_new
        else:
            return l

    ntext = ''
    for l in text.split('\n'):
        l = get_image_path(l)
        ntext += l + '\n'
    ntext = change_todo_square_chainbox_or_icon(ntext)
    return ntext


def get_youtube_embeds(text):
    ntext = ''

    for l in text.split('\n'):
        if l.strip().startswith('[yt:'):
            video_id = l.replace('[yt:','').replace(']','').strip()
            logger.info('youtube video detected: %s', video_id)
            l = '<iframe width="800" height="441" src="https://www.youtube.com/embed/' + video_id + '" frameborder="0" allowfullscreen></iframe>'
        ntext += l + '\n'
    return ntext


def right_link_from_dropbox_screenshot(text):
    """ changes the ending ?dl=0 of the link generated by Dropbox screenshoot in
    ?raw=1 to use the raw image instead of the dropbox page with the image"""
    changed = False
    for l in text.split('\n'):
        if l.find('?dl=0') != -1:
            text = text.replace('?dl=0', '?raw=1')
            logger.info('dropbox link detected')
            changed = True
    return text, changed
