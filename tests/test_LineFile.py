import threading
import random
import datetime
import multiprocessing
import json
import os
from server.models import LineFile


# One of tests is to find the performance of getting a line when multiple clients are requesting at the same time.as
# The test uses multiple processes to call get_line method.
class ConcurrentProcess(multiprocessing.Process):

    def __init__(self, data_obj, line_no, thread_no, event):
        self.data_obj = data_obj
        self.line_no = line_no
        self.thread_no = thread_no
        self.event = event
        super(ConcurrentProcess, self).__init__()

    def run(self):
        #while not self.event.is_set():
        self.event.wait()
        t1 = datetime.datetime.now()
        self.data_obj.get_line(self.line_no)
        t2 = datetime.datetime.now()

        print "Thread: {0}, line no: {1}, time: {2}".format(self.thread_no, self.line_no, str((t2-t1)))


# A test helper class for creating LineFile object and pre-process text file
class TestFile(object):

    @classmethod
    def load(cls, file_name):
        file = os.path.join(os.path.dirname(__file__), "test_data/" + file_name)
        ld = LineFile(file, 1000)
        ld.buildIndex()
        print "Building index for %s is done!" % file
        return ld


# The test class for testing the data model class - LineFile
class TestLineFile():

    # load the text file and build indexes first
    @classmethod
    def setup_class(cls):
        cls.test_data_small = TestFile.load("text_file_small.txt")
        cls.test_data_big = TestFile.load("text_file_1M_line.txt")

    def test_indexes_small_file(self):
        self.test_data_small.get_line(1)
        assert self.test_data_small.index_page == [0, 2, 4, 6, 8]

    def test_get_line_from_small_file(self):
        assert self.test_data_small.get_line(5) == (200, "e")
        assert self.test_data_small.get_line(0) == (404, None)
        assert self.test_data_small.get_line(6) == (404, None)
        assert self.test_data_small.get_line(1) == (200, "a")
        assert self.test_data_small.get_line("abc") == (500, "Woops! Something went wrong. Please try again")

    def test_indexes_big_file(self):
        assert self.test_data_big.indexing_completed == True

    def test_get_line_from_big_file_first_line(self):
        status, line = self.test_data_big.get_line(1)
        assert status == 200

    def test_get_line_from_big_file_last_line(self):
        status, line = self.test_data_big.get_line(1000000)
        assert status == 200

    def test_get_line_from_big_file_concurrently(self):
        result = []
        for num_of_concurrent_get_line in range(1, 20, 10):
            result.append(self.execute_concurrent_test(num_of_concurrent_get_line))
        print json.dumps(result)

    def execute_concurrent_test(self, num_of_concurrent_get_line):
        threads = []
        evt = multiprocessing.Event()
        for i in range(num_of_concurrent_get_line):
            line_no = random.randint(1, 5001)
            t = ConcurrentProcess(self.test_data_big, line_no, i, evt)
            threads.append(t)
            t.start()
        t1 = datetime.datetime.now()
        evt.set()
        for t in threads:
            t.join()
        t2 = datetime.datetime.now()
        return num_of_concurrent_get_line, (t2-t1).microseconds/1000/num_of_concurrent_get_line
