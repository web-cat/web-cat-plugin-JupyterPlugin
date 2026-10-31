"""
Pythy test framework for grading Python and Jupyter notebook submissions.
Modernized for Python 3.9 - 3.14+ compatibility without reliance on
deprecated libraries or private unittest internals.
"""

import io
import json
import os
import sys
import time
import traceback
import unittest


#~ Decorators .................................................................

def category(catname):
    """
    Specifies a category for a test case, which will be written in the result output.
    """
    def decorator(test_item):
        test_item.__pythytest_category__ = catname
        return test_item
    return decorator


#~ Global Runner Functions ....................................................

def runAllTests(stream=sys.stderr, timeoutCeiling=30):
    """
    Runs all test cases in suites that extend pythy.TestCase and writes
    JSON results to stream.
    """
    runner = TestRunner(stream)
    suite = unittest.TestSuite()

    def add_subclasses(cls):
        for child in cls.__subclasses__():
            suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(child))
            add_subclasses(child)

    add_subclasses(TestCase)
    runner.run(suite)


#~ Test Case Base Class .......................................................

class TestCase(unittest.TestCase):
    """
    Base test case for Web-CAT Python and Jupyter notebook grading.
    """
    locals = None
    output = None

    def setUp(self):
        if TestCase.locals is None:
            filename = self.student_file_name()
            TestCase.locals, TestCase.output = self.runFile(filename)

    def student_file_name(self):
        self.fail('Student file name is not defined.')

    def student_notebook(self):
        return None

    def lookup(self, name):
        if TestCase.locals is not None and name in TestCase.locals:
            return TestCase.locals[name]
        self.fail(f'Name "{name}" is not defined.')

    def runFile(self, filename='main.py', input_str=''):
        """
        Executes the student code file with captured stdin/stdout.
        Returns (student_globals, captured_output).
        """
        student_globals = {
            '__name__': '__main__',
            '__file__': os.path.abspath(filename),
            '__doc__': None,
        }

        capture_out = io.StringIO()
        inject_in = io.StringIO(input_str)

        old_stdout = sys.stdout
        old_stdin = sys.stdin
        sys.stdout = capture_out
        sys.stdin = inject_in

        try:
            with open(filename, 'r', encoding='utf-8', errors='replace') as fh:
                code_text = fh.read() + '\n'

            # Ensure pythy.sandbox is accessible if legacy assignments reference it
            try:
                import pythy.sandbox
            except ImportError:
                pass

            code_object = compile(code_text, filename, 'exec')
            exec(code_object, student_globals)
        finally:
            sys.stdout = old_stdout
            sys.stdin = old_stdin

        output = capture_out.getvalue()
        return student_globals, output

    def captureOutput(self, fn):
        capture_out = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = capture_out
        try:
            fn()
            return capture_out.getvalue()
        finally:
            sys.stdout = old_stdout

    # -------------------------------------------------------------
    # Media and Sound Assertions (VT Media computation libraries)
    # -------------------------------------------------------------
    def assertSoundsSimilar(self, expected, actual):
        length = actual.getLength()
        self.assertEqual(expected.getLength(), length)
        allowable_error = 0
        for i in range(length):
            actual_sample = actual.getSampleValueAt(i)
            expected_sample = expected.getSampleValueAt(i)
            if abs(actual_sample - expected_sample) > allowable_error:
                self.fail('Some samples do not have the expected values')

    def assertImagesSimilar(self, reason, expected, actual):
        width = actual.getWidth()
        height = actual.getHeight()

        self.assertEqual(
            expected.getWidth(), width,
            f"{reason}, the width of your final image was incorrect."
        )
        self.assertEqual(
            expected.getHeight(), height,
            f"{reason}, the height of your final image was incorrect."
        )

        allowable_error = 1
        red_errors = False
        green_errors = False
        blue_errors = False

        for r in range(height):
            for c in range(width):
                actual_pixel = actual.getPixel(c, r)
                expected_pixel = expected.getPixel(c, r)

                if abs(actual_pixel.getRed() - expected_pixel.getRed()) > allowable_error:
                    red_errors = True
                if abs(actual_pixel.getGreen() - expected_pixel.getGreen()) > allowable_error:
                    green_errors = True
                if abs(actual_pixel.getBlue() - expected_pixel.getBlue()) > allowable_error:
                    blue_errors = True

        channels = []
        if red_errors:
            channels.append('red')
        if green_errors:
            channels.append('green')
        if blue_errors:
            channels.append('blue')

        if channels:
            channel_str = ', '.join(channels) + ' components'
            self.fail(f'The {channel_str} contained some incorrect values.')


#~ Test Runner & Result .......................................................

class TestRunner:
    def __init__(self, stream=sys.stderr):
        self.stream = stream
        self.testData = {
            'categories': set(),
            'tests': []
        }

    def run(self, test):
        result = _PythyTestResult(self)
        test(result)
        self._dump_outcomes()
        return result

    def _dump_outcomes(self):
        self.testData['categories'] = list(self.testData['categories'])
        if TestCase.output is not None:
            self.testData['output'] = TestCase.output

        json.dump(self.testData, self.stream, indent=4)
        if hasattr(self.stream, 'flush'):
            self.stream.flush()

    def _startTest(self, test):
        method_name = getattr(test, '_testMethodName', str(test))
        newtest = {
            'name': test.id(),
            'description': method_name
        }

        short_desc = test.shortDescription()
        if short_desc:
            newtest['description'] = short_desc

        test_method = getattr(test, method_name, None)
        if test_method:
            category = getattr(test_method, '__pythytest_category__', None)
            if category:
                newtest['category'] = category
                self.testData['categories'].add(category)

            points = getattr(test_method, 'points', None)
            if points is not None:
                newtest['points'] = points

            nbgrader_id = getattr(test_method, 'nbgrader_id', None)
            if nbgrader_id:
                newtest['nbgrader_id'] = nbgrader_id

        self.testData['tests'].append(newtest)
        return newtest


class _PythyTestResult(unittest.TestResult):
    """
    Captures test outcomes and formats them for Web-CAT JSON consumption.
    """
    def __init__(self, runner):
        super().__init__()
        self.runner = runner
        self.currentTest = None

    def startTest(self, test):
        super().startTest(test)
        self.currentTest = self.runner._startTest(test)

    def addSuccess(self, test):
        super().addSuccess(test)
        if self.currentTest:
            self.currentTest["result"] = "success"

    def addFailure(self, test, err):
        super().addFailure(test, err)
        if self.currentTest:
            self.currentTest["result"] = "failure"
            self._populate_error(err)

    def addError(self, test, err):
        super().addError(test, err)
        if self.currentTest:
            self.currentTest["result"] = "error"
            self._populate_error(err)

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        if self.currentTest:
            self.currentTest["result"] = "skipped"
            self.currentTest["reason"] = str(reason)

    def _populate_error(self, err):
        exctype, val, tb = err
        if exctype.__name__ == 'AssertionError':
            self.currentTest["reason"] = str(val) if str(val) else 'AssertionError'
        else:
            self.currentTest["exception"] = exctype.__name__
            self.currentTest["reason"] = f"{exctype.__name__}: {str(val)}"

        # Extract and format clean traceback frames
        tb_entries = traceback.extract_tb(tb)
        filtered_frames = []
        for entry in tb_entries:
            filename = entry.filename
            # Filter out standard library unittest, importlib, and pythy runner internals
            if 'unittest' in filename or 'pythy' in filename or 'importlib' in filename:
                continue
            base = os.path.basename(filename)
            frame_str = f"{entry.name} ({base}:{entry.lineno})"
            filtered_frames.append(frame_str)

        self.currentTest["traceback"] = filtered_frames[:20]
