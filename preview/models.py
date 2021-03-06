
import tempfile

from os.path import getsize, basename
from os.path import join as pathjoin

from cached_property import cached_property

from preview.utils import safe_remove, get_extension
from preview.config import FILE_ROOT


class PathModel(object):
    def __init__(self, path):
        self._path = path

    def __repr__(self):
        return '<PathModel: %s>' % self.path

    @property
    def path(self):
        return self._path

    @property
    def size(self):
        return getsize(self._path)

    @cached_property
    def is_temp(self):
        return self._path.startswith(tempfile.tempdir)

    @cached_property
    def is_shared(self):
        return self._path.startswith(FILE_ROOT)

    @cached_property
    def extension(self):
        return get_extension(self._path)

    def safe_remove(self):
        safe_remove(self._path)

    def cleanup(self):
        if self.is_temp:
            self.safe_remove()


class PreviewModel(object):
    def __init__(self, path, width, height, format, origin=None, name=None,
                 args=None):
        self._width = width
        self._height = height
        self._format = format
        self._origin = origin
        self._name = name or basename(origin)
        self._src = PathModel(path)
        self._dst = None
        self._args = {}
        if args:
            self._args.update(args)

    def __repr__(self):
        dst_path = getattr(self.dst, 'path', None)
        return '<PreviewModel: %s, %s->%s, %ix%i>' % (
            self.name, self.src.path, dst_path, self.width, self.height)

    @property
    def content_type(self):
        return 'application/pdf' if self.format == 'pdf' else 'image/gif'

    @property
    def origin(self):
        'The parameter received from caller.'
        return self._origin

    @property
    def name(self):
        'The name of the file from caller'
        return self._name

    @cached_property
    def extension(self):
        return get_extension(self._name).lower()

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def format(self):
        return self._format

    @property
    def src(self):
        'The file to be previewed'
        return self._src

    @src.setter
    def src(self, obj):
        if self._src is not None:
            self._src.cleanup()
        # Reset attributes related to src.
        self._origin = obj.path
        self._name = basename(obj.path)
        # Clear extension cache.
        self.__dict__.pop('extension', None)
        self._src = obj

    @property
    def dst(self):
        'The generated preview'
        return self._dst

    @dst.setter
    def dst(self, obj):
        if self._dst is not None:
            self._dst.cleanup()
        self._dst = obj

    @property
    def args(self):
        return self._args

    def cleanup(self):
        'Removes temporary files.'
        if self._src is not None:
            self._src.cleanup()
        if self._dst is not None:
            self._dst.cleanup()
