# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2007 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2006-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Sylvain Taverne <sylvain@itaapy.com>
# Copyright (C) 2008 Nicolas Deram <nicolas@itaapy.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Import from itools
from itools.datatypes import Integer
from itools.gettext import MSG
from itools.handlers import Image as ImageFile
from itools.handlers import TARFile, ZIPFile, GzipFile, Bzip2File
from itools.odf import SXWFile, SXCFile, SXIFile, ODTFile, ODSFile, ODPFile
from itools.pdf import PDFFile
from itools.stl import stl
from itools.web import BaseView, STLView
from itools.xml import MSWord as MSWordFile, MSExcel as MSExcelFile
from itools.xml import MSPowerPoint as MSPowerPointFile, RTF as RTFFile

# Import from ikaaro
from file import File
from registry import register_object_class



###########################################################################
# Image / Video / Flash
###########################################################################
class ImageThumbnail(BaseView):

    access = True


    def get_mtime(self, resource):
        return resource.get_mtime()


    def GET(self, resource, context):
        width = context.get_form_value('width', type=Integer, default=48)
        height = context.get_form_value('height', type=Integer, default=48)

        data, format = resource.handler.get_thumbnail(width, height)
        if data is None:
            object = resource.get_resource('/ui/icons/48x48/image.png')
            data = object.to_str()
            format = 'png'

        response = context.response
        response.set_header('Content-Type', 'image/%s' % format)
        return data



class ImageView(STLView):

    access = 'is_allowed_to_view'
    title = MSG(u'View')
    template = '/ui/binary/Image_view.xml'

    def get_namespace(self, resource, context):
        if context.uri.path.endswith_slash:
            return {'src': ';download'}
        return {'src': '%s/;download' % resource.name}



# FIXME This is broken, check http://alistapart.com/articles/byebyeembed
class VideoView(STLView):

    access = 'is_allowed_to_view'
    title = MSG(u'View')
    template = '/ui/binary/Video_view.xml'


    def get_namespace(self, resource, context):
        return {'format': resource.handler.get_mimetype()}



class Image(File):

    class_id = 'image'
    class_version = '20071216'
    class_title = MSG(u'Image')
    class_icon16 = 'icons/16x16/image.png'
    class_icon48 = 'icons/48x48/image.png'
    class_views = ['view', 'download', 'externaledit', 'upload', 'backlinks',
                   'edit_metadata', 'edit_state', 'history']
    class_handler = ImageFile
    # Views
    thumb = ImageThumbnail()
    view = ImageView()



class Video(File):

    class_id = 'video'
    class_version = '20071216'
    class_title = MSG(u'Video')
    class_description = MSG(u'Video')
    class_icon16 = 'icons/16x16/flash.png'
    class_icon48 = 'icons/48x48/flash.png'
    # Views
    view = VideoView()



class Flash(File):

    class_id = 'application/x-shockwave-flash'
    class_version = '20071216'
    class_title = MSG(u'Flash')
    class_description = MSG(u'Flash Document')
    class_icon16 = 'icons/16x16/flash.png'
    class_icon48 = 'icons/48x48/flash.png'


    view = STLView(
        access='is_allowed_to_view',
        title=MSG(u'View'),
        template='/ui/binary/Flash_view.xml')



###########################################################################
# Office Documents
###########################################################################
class MSWord(File):

    class_id = 'application/msword'
    class_version = '20071216'
    class_title = MSG(u'Word')
    class_description = MSG(u'Word Text')
    class_icon16 = 'icons/16x16/word.png'
    class_icon48 = 'icons/48x48/word.png'
    class_handler = MSWordFile



class MSExcel(File):

    class_id = 'application/vnd.ms-excel'
    class_version = '20071216'
    class_title = MSG(u'Excel')
    class_description = MSG(u'Excel Spreadsheet')
    class_icon16 = 'icons/16x16/excel.png'
    class_icon48 = 'icons/48x48/excel.png'
    class_handler = MSExcelFile



class MSPowerPoint(File):

    class_id = 'application/vnd.ms-powerpoint'
    class_version = '20071216'
    class_title = MSG(u'PowerPoint')
    class_description = MSG(u'PowerPoint Presentation')
    class_icon16 = 'icons/16x16/powerpoint.png'
    class_icon48 = 'icons/48x48/powerpoint.png'
    class_handler = MSPowerPointFile



class OOWriter(File):

    class_id = 'application/vnd.sun.xml.writer'
    class_version = '20071216'
    class_title = MSG(u'OOo Writer')
    class_description = MSG(u'OpenOffice.org Text')
    class_icon16 = 'icons/16x16/oowriter.png'
    class_icon48 = 'icons/48x48/oowriter.png'
    class_handler = SXWFile



class OOCalc(File):

    class_id = 'application/vnd.sun.xml.calc'
    class_version = '20071216'
    class_title = MSG(u'OOo Calc')
    class_description = MSG(u'OpenOffice.org Spreadsheet')
    class_icon16 = 'icons/16x16/oocalc.png'
    class_icon48 = 'icons/48x48/oocalc.png'
    class_handler = SXCFile



class OOImpress(File):

    class_id = 'application/vnd.sun.xml.impress'
    class_version = '20071216'
    class_title = MSG(u'OOo Impress')
    class_description = MSG(u'OpenOffice.org Presentation')
    class_icon16 = 'icons/16x16/ooimpress.png'
    class_icon48 = 'icons/48x48/ooimpress.png'
    class_handler = SXIFile



class PDF(File):

    class_id = 'application/pdf'
    class_version = '20071216'
    class_title = MSG(u'PDF')
    class_description = MSG(u'PDF Document')
    class_icon16 = 'icons/16x16/pdf.png'
    class_icon48 = 'icons/48x48/pdf.png'
    class_handler = PDFFile



class RTF(File):

    class_id = 'text/rtf'
    class_version = '20071216'
    class_title = MSG(u"RTF")
    class_description = MSG(u'RTF Document')
    class_icon16 = 'icons/16x16/text.png'
    class_icon48 = 'icons/48x48/text.png'
    class_handler = RTFFile



class ODT(File):

    class_id = 'application/vnd.oasis.opendocument.text'
    class_version = '20071216'
    class_title = MSG(u'ODT')
    class_description = MSG(u'OpenDocument Text')
    class_icon16 = 'icons/16x16/odt.png'
    class_icon48 = 'icons/48x48/odt.png'
    class_handler = ODTFile



class ODS(File):

    class_id = 'application/vnd.oasis.opendocument.spreadsheet'
    class_version = '20071216'
    class_title = MSG(u'ODS')
    class_description = MSG(u'OpenDocument Spreadsheet')
    class_icon16 = 'icons/16x16/ods.png'
    class_icon48 = 'icons/48x48/ods.png'
    class_handler = ODSFile



class ODP(File):

    class_id = 'application/vnd.oasis.opendocument.presentation'
    class_version = '20071216'
    class_title = MSG(u'ODP')
    class_description = MSG(u'OpenDocument Presentation')
    class_icon16 = 'icons/16x16/odp.png'
    class_icon48 = 'icons/48x48/odp.png'
    class_handler = ODPFile



###########################################################################
# Archives
###########################################################################

class ArchiveView(STLView):

    access = 'is_allowed_to_view'
    title = MSG(u'View')
    template = '/ui/binary/Archive_view.xml'

    def get_namespace(self, resource, context):
        contents = resource.handler.get_contents()
        return {
            'contents': '\n'.join(contents)}


class Archive(File):

    view = ArchiveView()



class ZipArchive(Archive):

    class_id = 'application/zip'
    class_version = '20071216'
    class_title = MSG(u"Zip")
    class_description = MSG(u'Zip Archive')
    class_icon16 = 'icons/16x16/zip.png'
    class_icon48 = 'icons/48x48/zip.png'
    class_handler = ZIPFile



class TarArchive(Archive):

    class_id = 'application/x-tar'
    class_version = '20071216'
    class_title = MSG(u"Tar")
    class_description = MSG(u'Tar Archive')
    class_icon16 = 'icons/16x16/tar.png'
    class_icon48 = 'icons/48x48/tar.png'
    class_handler = TARFile



###########################################################################
# Compression
###########################################################################
class Gzip(File):

    class_id = 'application/x-gzip'
    class_version = '20071216'
    class_title = MSG(u"Gzip")
    class_description = MSG(u'Gzip Compressed')
    class_icon16 = 'icons/16x16/gzip.png'
    class_icon48 = 'icons/48x48/gzip.png'
    class_handler = GzipFile



class Bzip2(File):

    class_id = 'application/x-bzip2'
    class_version = '20071216'
    class_title = MSG(u"Bzip2")
    class_description = MSG(u'Bzip2 Compressed')
    class_icon16 = 'icons/16x16/bzip.png'
    class_icon48 = 'icons/48x48/bzip.png'
    class_handler = Bzip2File



###########################################################################
# Register
###########################################################################
register_object_class(Image)
register_object_class(Video)
register_object_class(Flash)
register_object_class(MSWord)
register_object_class(MSExcel)
register_object_class(MSPowerPoint)
register_object_class(PDF)
register_object_class(RTF)
# OpenOffice.org1.0 Format
register_object_class(OOWriter)
register_object_class(OOCalc)
register_object_class(OOImpress)
# OpenOffice.org2.0 Format (ODF)
register_object_class(ODT)
register_object_class(ODS)
register_object_class(ODP)
# Archives
register_object_class(ZipArchive)
register_object_class(TarArchive)
# Compression
register_object_class(Gzip)
register_object_class(Bzip2)
