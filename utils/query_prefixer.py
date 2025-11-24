import inspect
import os

from sqlalchemy import event


class FilenamePrefixer:
    """
    Prefix executed SQL queries with filename, line number, and function name.
    Helps debug where queries are coming from.
    ref: https://docs.sqlalchemy.org/en/20/core/events.html
    """

    def __init__(
        self,
        include_line_number=True,
        include_function_name=True,
        full_path=True,
    ):
        self.caller_info = None
        self.include_line_number = include_line_number
        self.include_function_name = include_function_name
        self.full_path = full_path
        self.skip_patterns = [
            "sqlalchemy",
            "sqlmodel",
            "site-packages",
            "contextlib.py",
            "threading.py",
            "distutils",
            "importlib",
        ]

    def find_real_caller(self):
        for frame_info in inspect.stack()[2:]:
            filename = frame_info.filename
            if not any(k in filename for k in self.skip_patterns):
                return {
                    "filename": filename
                    if self.full_path
                    else os.path.basename(filename),
                    "lineno": frame_info.lineno,
                    "function": frame_info.function,
                }
        return None

    def before_execute_handler(self, conn, clauseelement, multiparams, params):
        # Find the real caller of the query
        self.caller_info = self.find_real_caller()

    def before_cursor_execute_handler(
        self, conn, cursor, statement, parameters, context, executemany
    ):
        # Allows modification of the statement and parameters to be sent to the database
        stmt_upper = statement.strip().upper()
        if stmt_upper.startswith(("BEGIN", "COMMIT", "ROLLBACK", "SET ", "PRAGMA")):
            return statement, parameters
        if statement.strip().startswith("/*"):
            return statement, parameters
        if self.caller_info:
            parts = [self.caller_info["filename"]]
            if self.include_line_number:
                parts[0] += f":{self.caller_info['lineno']}"
            if self.include_function_name:
                parts.append(f"func:{self.caller_info['function']}")
            comment = f"/* {' '.join(parts)} */ "
            return comment + statement, parameters
        return statement, parameters

    def register(self, engine):
        event.listens_for(engine, "before_execute")(self.before_execute_handler)
        event.listens_for(engine, "before_cursor_execute", retval=True)(
            self.before_cursor_execute_handler
        )
