// Copyright (C) 2022 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only


#ifndef SBK_QTWEBSOCKETS_PYTHON_H
#define SBK_QTWEBSOCKETS_PYTHON_H

#include <sbkpython.h>
#include <sbkmodule.h>
#include <sbkconverter.h>
// Module Includes
#include <pyside6_qtcore_python.h>
#include <pyside6_qtnetwork_python.h>

// Bound library includes
#include <QtWebSockets/qwebsocketprotocol.h>
#include <QtWebSockets/qwebsocketserver.h>

QT_BEGIN_NAMESPACE
class QMaskGenerator;
class QWebSocket;
class QWebSocketCorsAuthenticator;
class QWebSocketHandshakeOptions;
QT_END_NAMESPACE

// Type indices
enum : int {
    SBK_QMaskGenerator_IDX                                   = 0,
    SBK_QWebSocket_IDX                                       = 1,
    SBK_QWebSocketCorsAuthenticator_IDX                      = 2,
    SBK_QWebSocketHandshakeOptions_IDX                       = 3,
    SBK_QWebSocketProtocol_Version_IDX                       = 6,
    SBK_QWebSocketProtocol_CloseCode_IDX                     = 5,
    SBK_QtWebSocketsQWebSocketProtocol_IDX                   = 4,
    SBK_QWebSocketServer_SslMode_IDX                         = 8,
    SBK_QWebSocketServer_IDX                                 = 7,
    SBK_QtWebSockets_IDX_COUNT                               = 9,
};

// This variable stores all Python types exported by this module.
extern Shiboken::Module::TypeInitStruct *SbkPySide6_QtWebSocketsTypeStructs;

// This variable stores the Python module object exported by this module.
extern PyObject *SbkPySide6_QtWebSocketsModuleObject;

// This variable stores all type converters exported by this module.
extern SbkConverter **SbkPySide6_QtWebSocketsTypeConverters;

// Converter indices
enum [[deprecated]] : int {
    SBK_QTWEBSOCKETS_QLIST_INT_IDX                           = 0, // QList<int>
    SBK_QTWEBSOCKETS_QLIST_QSSLERROR_IDX                     = 1, // QList<QSslError>
    SBK_QTWEBSOCKETS_QLIST_QWEBSOCKETPROTOCOL_VERSION_IDX    = 2, // QList<QWebSocketProtocol::Version>
    SBK_QTWEBSOCKETS_QLIST_QVARIANT_IDX                      = 3, // QList<QVariant>
    SBK_QTWEBSOCKETS_QLIST_QSTRING_IDX                       = 4, // QList<QString>
    SBK_QTWEBSOCKETS_QMAP_QSTRING_QVARIANT_IDX               = 5, // QMap<QString,QVariant>
    SBK_QTWEBSOCKETS_CONVERTERS_IDX_COUNT                    = 6,
};

// Converter indices
enum : int {
    SBK_QtWebSockets_QList_int_IDX                           = 0, // QList<int>
    SBK_QtWebSockets_QList_QSslError_IDX                     = 1, // QList<QSslError>
    SBK_QtWebSockets_QList_QWebSocketProtocol_Version_IDX    = 2, // QList<QWebSocketProtocol::Version>
    SBK_QtWebSockets_QList_QVariant_IDX                      = 3, // QList<QVariant>
    SBK_QtWebSockets_QList_QString_IDX                       = 4, // QList<QString>
    SBK_QtWebSockets_QMap_QString_QVariant_IDX               = 5, // QMap<QString,QVariant>
    SBK_QtWebSockets_CONVERTERS_IDX_COUNT                    = 6,
};
// Macros for type check

QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
namespace Shiboken
{

// PyType functions, to get the PyObjectType for a type T
template<> inline PyTypeObject *SbkType< ::QMaskGenerator >() { return Shiboken::Module::get(SbkPySide6_QtWebSocketsTypeStructs[SBK_QMaskGenerator_IDX]); }
template<> inline PyTypeObject *SbkType< ::QWebSocket >() { return Shiboken::Module::get(SbkPySide6_QtWebSocketsTypeStructs[SBK_QWebSocket_IDX]); }
template<> inline PyTypeObject *SbkType< ::QWebSocketCorsAuthenticator >() { return Shiboken::Module::get(SbkPySide6_QtWebSocketsTypeStructs[SBK_QWebSocketCorsAuthenticator_IDX]); }
template<> inline PyTypeObject *SbkType< ::QWebSocketHandshakeOptions >() { return Shiboken::Module::get(SbkPySide6_QtWebSocketsTypeStructs[SBK_QWebSocketHandshakeOptions_IDX]); }
template<> inline PyTypeObject *SbkType< ::QWebSocketProtocol::Version >() { return Shiboken::Module::get(SbkPySide6_QtWebSocketsTypeStructs[SBK_QWebSocketProtocol_Version_IDX]); }
template<> inline PyTypeObject *SbkType< ::QWebSocketProtocol::CloseCode >() { return Shiboken::Module::get(SbkPySide6_QtWebSocketsTypeStructs[SBK_QWebSocketProtocol_CloseCode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QWebSocketServer::SslMode >() { return Shiboken::Module::get(SbkPySide6_QtWebSocketsTypeStructs[SBK_QWebSocketServer_SslMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QWebSocketServer >() { return Shiboken::Module::get(SbkPySide6_QtWebSocketsTypeStructs[SBK_QWebSocketServer_IDX]); }

} // namespace Shiboken

QT_WARNING_POP
#endif // SBK_QTWEBSOCKETS_PYTHON_H

