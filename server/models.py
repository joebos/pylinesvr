import sys
import logging
import json
import os
import hashlib
from utils.tools import ErrorUtil, FileUtil


# LineFile is the data model class which encapsulate text file pre-processing and accessing.
# Pre-processing scan a text file line by line, and build an index to achieve O(1) operation for GET

# The index is similar to the cluster index we see in relational database.
# The key (primary key) is the line number, and the value is the file offset of a line from the start of the text file.

# In order to deal with a large number of lines where all the line numbers could not fit in memory,
# the system splits the index into index page files.
# Each index page file stores the file offsets for m number of lines (m is configurable in configuration.go).
# If a text file has more than m lines, the system does n/m to determine which index file,
# and use n % m to get the index(file offset) for line n from that index file.

class LineFile(object):

    def __init__(self, file_path, num_of_lines_per_index_page):
        self.file_path = file_path
        self.file_dir = os.path.dirname(os.path.abspath(file_path))
        self.file_path_hash = hashlib.sha256(self.file_path).hexdigest()
        self.index_page = []
        self.indexing_completed = False
        self.num_lines = 0
        self.num_of_lines_per_index_page = num_of_lines_per_index_page
        self.current_index_page = -1

    # The method for building index before starting the server
    def buildIndex(self):
        index_page_size = self.num_of_lines_per_index_page
        with open(self.file_path, "r") as line_file:

            logger = logging.getLogger(__name__)
            logger.info("Building indexes: %s" % str(self.file_path))
            self.__delete_index_files()

            last_pos = 0
            i = 0
            line = line_file.readline()
            while line:
                self.index_page.append(last_pos)
                last_pos = line_file.tell()
                if (i + 1) % index_page_size == 0:
                    self.__write_to_index_page(i/index_page_size)
                    del self.index_page[:]
                i += 1
                line = line_file.readline()
            if len(self.index_page) > 0:
                self.__write_to_index_page((i - 1)/index_page_size)
                del self.index_page[:]
            self.num_lines = i
            self.indexing_completed = True
            logger.info("Building indexes is completed: %s" % str(self.file_path))

    # Delete index files before building
    def __delete_index_files(self):
        file_prefix = self.file_path_hash
        FileUtil.delete_files(self.file_dir, "{0}_[0-9]+\.idx".format(file_prefix))

    # All index files are stored in a sub-folder called index under where the text file is located to support multiple files at the same time
    # For example, automated unit tests could use multiple text files for testing and we don't want index file name collision.
    # The name of an index file consists of the hash of text file path, and an integer number
    # which equals to n/m where n is the line number and m is the number of lines handled by each index page
    def __get_index_file_path(self, index_page_number):
        file_prefix = self.file_path_hash
        folder = os.path.join(self.file_dir, "index")
        if not os.path.exists(folder):
            os.makedirs(folder)
        index_file_path = os.path.join(folder, "{0}_{1}.idx".format(file_prefix, index_page_number))
        return index_file_path

    def __write_to_index_page(self, index_page_number):
        index_file_path = self.__get_index_file_path(index_page_number)
        with open(index_file_path, "w") as index_file:
            json.dump(self.index_page, index_file)

    # If an index page file is not in memory, load it
    def __load_index_page(self, index_page_number):
        index_file_path = self.__get_index_file_path(index_page_number)
        with open(index_file_path, "r") as index_file:
            self.index_page = json.load(index_file)
            self.current_index_page = index_page_number
            logger = logging.getLogger(__name__)
            logger.info("The size of the index page {0}: {1}, # of lines: {2}".format(index_page_number, sys.getsizeof(self.index_page), self.num_lines))

    # GetLine is the method for retrieving a line. It first finds which index page file,
    # then get the file offset of the line, and then open the text file, seek to that offset and read the entire line
    def get_line(self, line_no):
        try:
            if not self.indexing_completed:
                self.buildIndex()
            line_number0 = int(line_no) - 1
            if line_number0 >=0 and line_number0 < self.num_lines:
                index_page_number = line_number0 / self.num_of_lines_per_index_page
                if index_page_number != self.current_index_page:
                    self.__load_index_page(index_page_number)
                line_address = self.index_page[line_number0 % self.num_of_lines_per_index_page]
                with open(self.file_path, "r") as line_file:
                    line_file.seek(line_address)
                    line = line_file.readline()
                    if line:
                        line = line.strip()
                        return 200, line
            return 404, None
        except Exception, arg:
            error = ErrorUtil.get_error(arg)
            logger = logging.getLogger(__name__)
            logger.error(json.dumps(error, indent=4, sort_keys=True))
            return 500, "Woops! Something went wrong. Please try again"



