// Copyright (C) 2022 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only


#ifndef SBK_QTPDFWIDGETS_PYTHON_H
#define SBK_QTPDFWIDGETS_PYTHON_H

#include <sbkpython.h>
#include <sbkmodule.h>
#include <sbkconverter.h>
// Module Includes
#include <pyside6_qtcore_python.h>
#include <pyside6_qtgui_python.h>
#include <pyside6_qtwidgets_python.h>
#include <pyside6_qtpdf_python.h>

// Bound library includes
#include <QtPdfWidgets/qpdfview.h>

QT_BEGIN_NAMESPACE
class QPdfPageSelector;
QT_END_NAMESPACE

// Type indices
enum : int {
    SBK_QPdfPageSelector_IDX                                 = 0,
    SBK_QPdfView_PageMode_IDX                                = 2,
    SBK_QPdfView_ZoomMode_IDX                                = 3,
    SBK_QPdfView_IDX                                         = 1,
    SBK_QtPdfWidgets_IDX_COUNT                               = 4,
};

// This variable stores all Python types exported by this module.
extern Shiboken::Module::TypeInitStruct *SbkPySide6_QtPdfWidgetsTypeStructs;

// This variable stores the Python module object exported by this module.
extern PyObject *SbkPySide6_QtPdfWidgetsModuleObject;

// This variable stores all type converters exported by this module.
extern SbkConverter **SbkPySide6_QtPdfWidgetsTypeConverters;

// Converter indices
enum [[deprecated]] : int {
    SBK_QTPDFWIDGETS_QLIST_INT_IDX                           = 0, // QList<int>
    SBK_QTPDFWIDGETS_QLIST_QVARIANT_IDX                      = 1, // QList<QVariant>
    SBK_QTPDFWIDGETS_QLIST_QSTRING_IDX                       = 2, // QList<QString>
    SBK_QTPDFWIDGETS_QMAP_QSTRING_QVARIANT_IDX               = 3, // QMap<QString,QVariant>
    SBK_QTPDFWIDGETS_CONVERTERS_IDX_COUNT                    = 4,
};

// Converter indices
enum : int {
    SBK_QtPdfWidgets_QList_int_IDX                           = 0, // QList<int>
    SBK_QtPdfWidgets_QList_QVariant_IDX                      = 1, // QList<QVariant>
    SBK_QtPdfWidgets_QList_QString_IDX                       = 2, // QList<QString>
    SBK_QtPdfWidgets_QMap_QString_QVariant_IDX               = 3, // QMap<QString,QVariant>
    SBK_QtPdfWidgets_CONVERTERS_IDX_COUNT                    = 4,
};
// Macros for type check

QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
namespace Shiboken
{

// PyType functions, to get the PyObjectType for a type T
template<> inline PyTypeObject *SbkType< ::QPdfPageSelector >() { return Shiboken::Module::get(SbkPySide6_QtPdfWidgetsTypeStructs[SBK_QPdfPageSelector_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPdfView::PageMode >() { return Shiboken::Module::get(SbkPySide6_QtPdfWidgetsTypeStructs[SBK_QPdfView_PageMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPdfView::ZoomMode >() { return Shiboken::Module::get(SbkPySide6_QtPdfWidgetsTypeStructs[SBK_QPdfView_ZoomMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPdfView >() { return Shiboken::Module::get(SbkPySide6_QtPdfWidgetsTypeStructs[SBK_QPdfView_IDX]); }

} // namespace Shiboken

QT_WARNING_POP
#endif // SBK_QTPDFWIDGETS_PYTHON_H

