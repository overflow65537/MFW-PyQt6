// Copyright (C) 2022 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only


#ifndef SBK_QTWEBCHANNEL_PYTHON_H
#define SBK_QTWEBCHANNEL_PYTHON_H

#include <sbkpython.h>
#include <sbkmodule.h>
#include <sbkconverter.h>
// Module Includes
#include <pyside6_qtcore_python.h>

// Bound library includes

QT_BEGIN_NAMESPACE
class QWebChannel;
class QWebChannelAbstractTransport;
QT_END_NAMESPACE

// Type indices
enum : int {
    SBK_QWebChannel_IDX                                      = 0,
    SBK_QWebChannelAbstractTransport_IDX                     = 1,
    SBK_QtWebChannel_IDX_COUNT                               = 2,
};

// This variable stores all Python types exported by this module.
extern Shiboken::Module::TypeInitStruct *SbkPySide6_QtWebChannelTypeStructs;

// This variable stores the Python module object exported by this module.
extern PyObject *SbkPySide6_QtWebChannelModuleObject;

// This variable stores all type converters exported by this module.
extern SbkConverter **SbkPySide6_QtWebChannelTypeConverters;

// Converter indices
enum [[deprecated]] : int {
    SBK_QTWEBCHANNEL_QLIST_INT_IDX                           = 0, // QList<int>
    SBK_QTWEBCHANNEL_QHASH_QSTRING_QOBJECTPTR_IDX            = 1, // QHash<QString,QObject*>
    SBK_QTWEBCHANNEL_QLIST_QVARIANT_IDX                      = 2, // QList<QVariant>
    SBK_QTWEBCHANNEL_QLIST_QSTRING_IDX                       = 3, // QList<QString>
    SBK_QTWEBCHANNEL_QMAP_QSTRING_QVARIANT_IDX               = 4, // QMap<QString,QVariant>
    SBK_QTWEBCHANNEL_CONVERTERS_IDX_COUNT                    = 5,
};

// Converter indices
enum : int {
    SBK_QtWebChannel_QList_int_IDX                           = 0, // QList<int>
    SBK_QtWebChannel_QHash_QString_QObjectPTR_IDX            = 1, // QHash<QString,QObject*>
    SBK_QtWebChannel_QList_QVariant_IDX                      = 2, // QList<QVariant>
    SBK_QtWebChannel_QList_QString_IDX                       = 3, // QList<QString>
    SBK_QtWebChannel_QMap_QString_QVariant_IDX               = 4, // QMap<QString,QVariant>
    SBK_QtWebChannel_CONVERTERS_IDX_COUNT                    = 5,
};
// Macros for type check

QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
namespace Shiboken
{

// PyType functions, to get the PyObjectType for a type T
template<> inline PyTypeObject *SbkType< ::QWebChannel >() { return Shiboken::Module::get(SbkPySide6_QtWebChannelTypeStructs[SBK_QWebChannel_IDX]); }
template<> inline PyTypeObject *SbkType< ::QWebChannelAbstractTransport >() { return Shiboken::Module::get(SbkPySide6_QtWebChannelTypeStructs[SBK_QWebChannelAbstractTransport_IDX]); }

} // namespace Shiboken

QT_WARNING_POP
#endif // SBK_QTWEBCHANNEL_PYTHON_H

