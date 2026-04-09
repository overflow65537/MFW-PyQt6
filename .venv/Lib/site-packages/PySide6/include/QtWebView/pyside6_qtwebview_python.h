// Copyright (C) 2022 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only


#ifndef SBK_QTWEBVIEW_PYTHON_H
#define SBK_QTWEBVIEW_PYTHON_H

#include <sbkpython.h>
#include <sbkmodule.h>
#include <sbkconverter.h>
// Module Includes
#include <pyside6_qtgui_python.h>
#include <pyside6_qtcore_python.h>

// Bound library includes
#include <QtWebView/qtwebviewfunctions.h>
#include <QtWebView/qwebviewloadinginfo.h>
#include <QtWebView/qwebviewsettings.h>

QT_BEGIN_NAMESPACE
class QWebView;
QT_END_NAMESPACE

// Type indices
enum : int {
    SBK_QWebView_IDX                                         = 0,
    SBK_QWebViewLoadingInfo_LoadStatus_IDX                   = 2,
    SBK_QWebViewLoadingInfo_IDX                              = 1,
    SBK_QWebViewSettings_WebAttribute_IDX                    = 4,
    SBK_QWebViewSettings_IDX                                 = 3,
    SBK_QtWebViewQtWebView_IDX                               = 5,
    SBK_QtWebView_IDX_COUNT                                  = 6,
};

// This variable stores all Python types exported by this module.
extern Shiboken::Module::TypeInitStruct *SbkPySide6_QtWebViewTypeStructs;

// This variable stores the Python module object exported by this module.
extern PyObject *SbkPySide6_QtWebViewModuleObject;

// This variable stores all type converters exported by this module.
extern SbkConverter **SbkPySide6_QtWebViewTypeConverters;

// Converter indices
enum [[deprecated]] : int {
    SBK_QTWEBVIEW_QLIST_INT_IDX                              = 0, // QList<int>
    SBK_QTWEBVIEW_QLIST_QVARIANT_IDX                         = 1, // QList<QVariant>
    SBK_QTWEBVIEW_QLIST_QSTRING_IDX                          = 2, // QList<QString>
    SBK_QTWEBVIEW_QMAP_QSTRING_QVARIANT_IDX                  = 3, // QMap<QString,QVariant>
    SBK_QTWEBVIEW_CONVERTERS_IDX_COUNT                       = 4,
};

// Converter indices
enum : int {
    SBK_QtWebView_QList_int_IDX                              = 0, // QList<int>
    SBK_QtWebView_QList_QVariant_IDX                         = 1, // QList<QVariant>
    SBK_QtWebView_QList_QString_IDX                          = 2, // QList<QString>
    SBK_QtWebView_QMap_QString_QVariant_IDX                  = 3, // QMap<QString,QVariant>
    SBK_QtWebView_CONVERTERS_IDX_COUNT                       = 4,
};
// Macros for type check

QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
namespace Shiboken
{

// PyType functions, to get the PyObjectType for a type T
template<> inline PyTypeObject *SbkType< ::QWebView >() { return Shiboken::Module::get(SbkPySide6_QtWebViewTypeStructs[SBK_QWebView_IDX]); }
template<> inline PyTypeObject *SbkType< ::QWebViewLoadingInfo::LoadStatus >() { return Shiboken::Module::get(SbkPySide6_QtWebViewTypeStructs[SBK_QWebViewLoadingInfo_LoadStatus_IDX]); }
template<> inline PyTypeObject *SbkType< ::QWebViewLoadingInfo >() { return Shiboken::Module::get(SbkPySide6_QtWebViewTypeStructs[SBK_QWebViewLoadingInfo_IDX]); }
template<> inline PyTypeObject *SbkType< ::QWebViewSettings::WebAttribute >() { return Shiboken::Module::get(SbkPySide6_QtWebViewTypeStructs[SBK_QWebViewSettings_WebAttribute_IDX]); }
template<> inline PyTypeObject *SbkType< ::QWebViewSettings >() { return Shiboken::Module::get(SbkPySide6_QtWebViewTypeStructs[SBK_QWebViewSettings_IDX]); }

} // namespace Shiboken

QT_WARNING_POP
#endif // SBK_QTWEBVIEW_PYTHON_H

