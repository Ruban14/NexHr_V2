"""Export domain models."""

from importlib import import_module

from apps.attendance.models.attendance import Attendance
from apps.attendance.models.session import AttendanceSession

# Module name `break` is a Python keyword; load via importlib.
AttendanceBreak = import_module('apps.attendance.models.break').AttendanceBreak

__all__ = ['Attendance', 'AttendanceSession', 'AttendanceBreak']
