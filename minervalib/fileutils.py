import os, logging, re

class FileUtils:

    @staticmethod
    def list_files(dir, filefilter):
        files = []
        for (dirpath, dirnames, filenames) in os.walk(dir):
            for filename in filenames:
                ext = os.path.splitext(filename)[1]
                if ext in filefilter:
                    files.append(os.path.join(dirpath, filename))

        logging.debug(files)
        return files

    _valid_name = re.compile('^[a-zA-Z][a-zA-Z0-9\\-_]+$')
    _length_name = 128

    @staticmethod
    def validate_name(s, object_type=None):
        if len(s) > FileUtils._length_name or FileUtils._valid_name.match(s) is None:
            raise ValueError('{} name is invalid. Valid names begin with a letter, '
                             'contain only alphanumeric characters, dash and '
                             'underscore. The maximum length '
                             'is {}'.format(object_type, FileUtils._length_name))
