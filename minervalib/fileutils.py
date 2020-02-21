import os, logging, re

class FileUtils:

    _valid_name = re.compile('^[a-zA-Z][a-zA-Z0-9\\-_]+$')
    _length_name = 128

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

    @staticmethod
    def list_files_regex(dir, pattern):
        files = []
        prog = re.compile(pattern)
        for filename in os.listdir(dir):
            if prog.match(filename):
                files.append(os.path.join(dir, filename))
            else:
                logging.info("(skip) Filename %s does not match tile pattern: %s", filename, pattern)

        logging.info(files)
        return files

    @staticmethod
    def validate_name(s, object_type=None):
        if len(s) > FileUtils._length_name or FileUtils._valid_name.match(s) is None:
            raise ValueError('{} name is invalid. Valid names begin with a letter, '
                             'contain only alphanumeric characters, dash and '
                             'underscore. The maximum length '
                             'is {}'.format(object_type, FileUtils._length_name))

    @staticmethod
    def get_key(filename):
        basename = os.path.basename(filename)
        path = os.path.dirname(filename)
        path = path.replace("\\", "/")
        path = re.sub("^[a-zA-Z]:", "", path)
        return path + '/' + basename
