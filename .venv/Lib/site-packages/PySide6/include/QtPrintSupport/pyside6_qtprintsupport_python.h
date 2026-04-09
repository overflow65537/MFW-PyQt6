// Copyright (C) 2022 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only


#ifndef SBK_QTPRINTSUPPORT_PYTHON_H
#define SBK_QTPRINTSUPPORT_PYTHON_H

#include <sbkpython.h>
#include <sbkmodule.h>
#include <sbkconverter.h>
// Module Includes
#include <pyside6_qtwidgets_python.h>
#include <pyside6_qtgui_python.h>
#include <pyside6_qtcore_python.h>

// Bound library includes
#include <QtPrintSupport/qabstractprintdialog.h>
#include <QtPrintSupport/qprintengine.h>
#include <QtPrintSupport/qprinter.h>
#include <QtPrintSupport/qprintpreviewwidget.h>

QT_BEGIN_NAMESPACE
class QPageSetupDialog;
class QPrintDialog;
class QPrintPreviewDialog;
class QPrinterInfo;
QT_END_NAMESPACE

// Type indices
enum : int {
    SBK_QAbstractPrintDialog_PrintRange_IDX                  = 2,
    SBK_QAbstractPrintDialog_PrintDialogOption_IDX           = 1,
    SBK_QFlags_QAbstractPrintDialog_PrintDialogOption_IDX    = 3,
    SBK_QAbstractPrintDialog_IDX                             = 0,
    SBK_QPageSetupDialog_IDX                                 = 4,
    SBK_QPrintDialog_IDX                                     = 5,
    SBK_QPrintEngine_PrintEnginePropertyKey_IDX              = 7,
    SBK_QPrintEngine_IDX                                     = 6,
    SBK_QPrintPreviewDialog_IDX                              = 8,
    SBK_QPrintPreviewWidget_ViewMode_IDX                     = 10,
    SBK_QPrintPreviewWidget_ZoomMode_IDX                     = 11,
    SBK_QPrintPreviewWidget_IDX                              = 9,
    SBK_QPrinter_PrinterMode_IDX                             = 19,
    SBK_QPrinter_PageOrder_IDX                               = 16,
    SBK_QPrinter_ColorMode_IDX                               = 13,
    SBK_QPrinter_PaperSource_IDX                             = 17,
    SBK_QPrinter_PrinterState_IDX                            = 20,
    SBK_QPrinter_OutputFormat_IDX                            = 15,
    SBK_QPrinter_PrintRange_IDX                              = 18,
    SBK_QPrinter_Unit_IDX                                    = 21,
    SBK_QPrinter_DuplexMode_IDX                              = 14,
    SBK_QPrinter_IDX                                         = 12,
    SBK_QPrinterInfo_IDX                                     = 22,
    SBK_QtPrintSupport_IDX_COUNT                             = 23,
};

// This variable stores all Python types exported by this module.
extern Shiboken::Module::TypeInitStruct *SbkPySide6_QtPrintSupportTypeStructs;

// This variable stores the Python module object exported by this module.
extern PyObject *SbkPySide6_QtPrintSupportModuleObject;

// This variable stores all type converters exported by this module.
extern SbkConverter **SbkPySide6_QtPrintSupportTypeConverters;

// Converter indices
enum [[deprecated]] : int {
    SBK_QTPRINTSUPPORT_QLIST_INT_IDX                         = 0, // QList<int>
    SBK_QTPRINTSUPPORT_QLIST_QPRINTERINFO_IDX                = 1, // QList<QPrinterInfo>
    SBK_QTPRINTSUPPORT_QLIST_QPRINTER_COLORMODE_IDX          = 2, // QList<QPrinter::ColorMode>
    SBK_QTPRINTSUPPORT_QLIST_QPRINTER_DUPLEXMODE_IDX         = 3, // QList<QPrinter::DuplexMode>
    SBK_QTPRINTSUPPORT_QLIST_QPAGESIZE_IDX                   = 4, // QList<QPageSize>
    SBK_QTPRINTSUPPORT_QLIST_QPRINTER_PAPERSOURCE_IDX        = 5, // QList<QPrinter::PaperSource>
    SBK_QTPRINTSUPPORT_QLIST_QWIDGETPTR_IDX                  = 6, // QList<QWidget*>
    SBK_QTPRINTSUPPORT_QLIST_QVARIANT_IDX                    = 7, // QList<QVariant>
    SBK_QTPRINTSUPPORT_QLIST_QSTRING_IDX                     = 8, // QList<QString>
    SBK_QTPRINTSUPPORT_QMAP_QSTRING_QVARIANT_IDX             = 9, // QMap<QString,QVariant>
    SBK_QTPRINTSUPPORT_CONVERTERS_IDX_COUNT                  = 10,
};

// Converter indices
enum : int {
    SBK_QtPrintSupport_QList_int_IDX                         = 0, // QList<int>
    SBK_QtPrintSupport_QList_QPrinterInfo_IDX                = 1, // QList<QPrinterInfo>
    SBK_QtPrintSupport_QList_QPrinter_ColorMode_IDX          = 2, // QList<QPrinter::ColorMode>
    SBK_QtPrintSupport_QList_QPrinter_DuplexMode_IDX         = 3, // QList<QPrinter::DuplexMode>
    SBK_QtPrintSupport_QList_QPageSize_IDX                   = 4, // QList<QPageSize>
    SBK_QtPrintSupport_QList_QPrinter_PaperSource_IDX        = 5, // QList<QPrinter::PaperSource>
    SBK_QtPrintSupport_QList_QWidgetPTR_IDX                  = 6, // QList<QWidget*>
    SBK_QtPrintSupport_QList_QVariant_IDX                    = 7, // QList<QVariant>
    SBK_QtPrintSupport_QList_QString_IDX                     = 8, // QList<QString>
    SBK_QtPrintSupport_QMap_QString_QVariant_IDX             = 9, // QMap<QString,QVariant>
    SBK_QtPrintSupport_CONVERTERS_IDX_COUNT                  = 10,
};
// Macros for type check

QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
namespace Shiboken
{

// PyType functions, to get the PyObjectType for a type T
template<> inline PyTypeObject *SbkType< ::QAbstractPrintDialog::PrintRange >() { return Shiboken::Module::get(SbkPySide6_QtPrintSupportTypeStructs[SBK_QAbstractPrintDialog_PrintRange_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractPrintDialog::PrintDialogOption >() { return Shiboken::Module::get(SbkPySide6_QtPrintSupportTypeStructs[SBK_QAbstractPrintDialog_PrintDialogOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QAbstractPrintDialog::PrintDialogOption> >() { return Shiboken::Module::get(SbkPySide6_QtPrintSupportTypeStructs[SBK_QFlags_QAbstractPrintDialog_PrintDialogOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractPrintDialog >() { return Shiboken::Module::get(SbkPySide6_QtPrintSupportTypeStructs[SBK_QAbstractPrintDialog_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPageSetupDialog >() { return Shiboken::Module::get(SbkPySide6_QtPrintSupportTypeStructs[SBK_QPageSetupDialog_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPrintDialog >() { return Shiboken::Module::get(SbkPySide6_QtPrintSupportTypeStructs[SBK_QPrintDialog_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPrintEngine::PrintEnginePropertyKey >() { return Shiboken::Module::get(SbkPySide6_QtPrintSupportTypeStructs[SBK_QPrintEngine_PrintEnginePropertyKey_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPrintEngine >() { return Shiboken::Module::get(SbkPySide6_QtPrintSupportTypeStructs[SBK_QPrintEngine_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPrintPreviewDialog >() { return Shiboken::Module::get(SbkPySide6_QtPrintSupportTypeStructs[SBK_QPrintPreviewDialog_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPrintPreviewWidget::ViewMode >() { return Shiboken::Module::get(SbkPySide6_QtPrintSupportTypeStructs[SBK_QPrintPreviewWidget_ViewMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPrintPreviewWidget::ZoomMode >() { return Shiboken::Module::get(SbkPySide6_QtPrintSupportTypeStructs[SBK_QPrintPreviewWidget_ZoomMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPrintPreviewWidget >() { return Shiboken::Module::get(SbkPySide6_QtPrintSupportTypeStructs[SBK_QPrintPreviewWidget_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPrinter::PrinterMode >() { return Shiboken::Module::get(SbkPySide6_QtPrintSupportTypeStructs[SBK_QPrinter_PrinterMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPrinter::PageOrder >() { return Shiboken::Module::get(SbkPySide6_QtPrintSupportTypeStructs[SBK_QPrinter_PageOrder_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPrinter::ColorMode >() { return Shiboken::Module::get(SbkPySide6_QtPrintSupportTypeStructs[SBK_QPrinter_ColorMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPrinter::PaperSource >() { return Shiboken::Module::get(SbkPySide6_QtPrintSupportTypeStructs[SBK_QPrinter_PaperSource_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPrinter::PrinterState >() { return Shiboken::Module::get(SbkPySide6_QtPrintSupportTypeStructs[SBK_QPrinter_PrinterState_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPrinter::OutputFormat >() { return Shiboken::Module::get(SbkPySide6_QtPrintSupportTypeStructs[SBK_QPrinter_OutputFormat_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPrinter::PrintRange >() { return Shiboken::Module::get(SbkPySide6_QtPrintSupportTypeStructs[SBK_QPrinter_PrintRange_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPrinter::Unit >() { return Shiboken::Module::get(SbkPySide6_QtPrintSupportTypeStructs[SBK_QPrinter_Unit_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPrinter::DuplexMode >() { return Shiboken::Module::get(SbkPySide6_QtPrintSupportTypeStructs[SBK_QPrinter_DuplexMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPrinter >() { return Shiboken::Module::get(SbkPySide6_QtPrintSupportTypeStructs[SBK_QPrinter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPrinterInfo >() { return Shiboken::Module::get(SbkPySide6_QtPrintSupportTypeStructs[SBK_QPrinterInfo_IDX]); }

} // namespace Shiboken

QT_WARNING_POP
#endif // SBK_QTPRINTSUPPORT_PYTHON_H

