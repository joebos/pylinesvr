
import traceback
import os
import sys
import logging
import re


class LoggingUtil(object):

    @classmethod
    def init_logging(cls):
        logging.basicConfig(
            format="%(asctime)s %(levelname)s %(threadName)s %(name)s: %(message)s",
            level=logging.INFO,
            handlers=[
                logging.FileHandler("{0}/{1}.log".format("../", "server")),
                logging.StreamHandler()
        ])


class ErrorUtil(object):

    @classmethod
    def __get_error_msgs(cls, args):
        err_msgs = []
        if isinstance(args, list) or isinstance(args, dict):
            for arg in args:
                err_msgs.append(str(arg))
        else:
            err_msgs.append(str(args))
        return err_msgs

    @classmethod
    def get_error(cls, arg):
        error = {}
        try:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            error["error_type"] = str(exc_type)
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            error["file"] = fname
            line = str(sys.exc_traceback.tb_lineno)
            error["line_no"] = line
            tb = traceback.format_exc()
            error["trace"] = tb
            error["message"] = cls.__get_error_msgs(arg)
            return error
        except Exception, arg:
            return error


class FileUtil(object):

    @classmethod
    def delete_files(cls, folder, file_regex):
        for f in os.listdir(folder):
            if re.search(file_regex, f):
                os.remove(os.path.join(folder, f))
