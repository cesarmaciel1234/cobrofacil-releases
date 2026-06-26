"""Helpers QPrinter / QTextDocument — compat PyQt6."""
from __future__ import annotations

from src.utils.qt_compat import IS_QT6


def _qprinter():
    if IS_QT6:
        from PyQt6.QtPrintSupport import QPrinter

        return QPrinter
    from PyQt5.QtPrintSupport import QPrinter

    return QPrinter


def _qprinterinfo():
    if IS_QT6:
        from PyQt6.QtPrintSupport import QPrinterInfo

        return QPrinterInfo
    from PyQt5.QtPrintSupport import QPrinterInfo

    return QPrinterInfo


def printer_high_resolution():
    QPrinter = _qprinter()
    if IS_QT6:
        return QPrinter.PrinterMode.HighResolution
    return QPrinter.HighResolution


def printer_pdf_format():
    QPrinter = _qprinter()
    if IS_QT6:
        return QPrinter.OutputFormat.PdfFormat
    return QPrinter.PdfFormat


def set_page_margins_mm(printer, left: float, top: float, right: float, bottom: float) -> None:
    if IS_QT6:
        from PyQt6.QtCore import QMarginsF
        from PyQt6.QtGui import QPageLayout

        printer.setPageMargins(
            QMarginsF(left, top, right, bottom),
            QPageLayout.Unit.Millimeter,
        )
        return
    QPrinter = _qprinter()
    printer.setPageMargins(left, top, right, bottom, QPrinter.Millimeter)


def set_page_orientation_portrait(printer) -> None:
    if IS_QT6:
        from PyQt6.QtGui import QPageLayout

        printer.setPageOrientation(QPageLayout.Orientation.Portrait)
        return
    QPrinter = _qprinter()
    printer.setOrientation(QPrinter.Portrait)


def print_document(doc, printer) -> None:
    if IS_QT6:
        doc.print(printer)
    else:
        doc.print_(printer)


def available_printer_names():
    QPrinterInfo = _qprinterinfo()
    if IS_QT6:
        return [p.printerName() for p in QPrinterInfo.availablePrinters()]
    return QPrinterInfo.availablePrinterNames()
