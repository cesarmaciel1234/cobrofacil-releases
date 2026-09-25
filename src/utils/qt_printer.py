"""Helpers QPrinter / QTextDocument — compat PyQt6."""
from __future__ import annotations

from src.utils.qt_compat import IS_QT6


def _qprinter():
    if IS_QT6:
        from PyQt6.QtPrintSupport import QPrinter

        return QPrinter
    from PyQt6.QtPrintSupport import QPrinter

    return QPrinter


def _qprinterinfo():
    if IS_QT6:
        from PyQt6.QtPrintSupport import QPrinterInfo

        return QPrinterInfo
    from PyQt6.QtPrintSupport import QPrinterInfo

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


def abrir_documento_pdf(pdf_path: str, margen_mm: float = 5, resolucion: int = 120):
    """Arma el PDF sin la impresora de Windows.

    QPrinter busca el plugin printsupport. En el ejecutable ese plugin no va,
    y Qt cierra el programa al generar la etiqueta.
    """
    from PyQt6.QtCore import QMarginsF, QSizeF
    from PyQt6.QtGui import QPageLayout, QPageSize, QPdfWriter, QTextDocument

    writer = QPdfWriter(pdf_path)
    writer.setResolution(int(resolucion))
    writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    writer.setPageMargins(
        QMarginsF(margen_mm, margen_mm, margen_mm, margen_mm),
        QPageLayout.Unit.Millimeter,
    )
    doc = QTextDocument()
    doc.setDefaultStyleSheet("body { background-color: #ffffff; color: #000000; }")
    doc.setDocumentMargin(0)
    ancho = int(writer.width() or 0)
    alto = int(writer.height() or 0)
    if ancho < 50 or alto < 50:
        ancho, alto = 794, 1123
    doc.setPageSize(QSizeF(float(ancho), float(alto)))
    return writer, doc


def available_printer_names():
    QPrinterInfo = _qprinterinfo()
    if IS_QT6:
        return [p.printerName() for p in QPrinterInfo.availablePrinters()]
    return QPrinterInfo.availablePrinterNames()
