import os, logging

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
