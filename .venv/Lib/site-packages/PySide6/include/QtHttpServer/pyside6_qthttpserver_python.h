// Copyright (C) 2022 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only


#ifndef SBK_QTHTTPSERVER_PYTHON_H
#define SBK_QTHTTPSERVER_PYTHON_H

#include <sbkpython.h>
#include <sbkmodule.h>
#include <sbkconverter.h>
// Module Includes
#include <pyside6_qtconcurrent_python.h>
#include <pyside6_qtcore_python.h>
#include <pyside6_qtwebsockets_python.h>
#include <pyside6_qtnetwork_python.h>

// Bound library includes
#include <QtHttpServer/qhttpserverrequest.h>
#include <QtHttpServer/qhttpserverresponder.h>
#include <QtHttpServer/qhttpserverwebsocketupgraderesponse.h>
#if QT_CONFIG(future)
#include <QtCore/qfuture.h>
#endif

QT_BEGIN_NAMESPACE
class QAbstractHttpServer;
class QHttpServer;
class QHttpServerConfiguration;
class QHttpServerResponse;
class QHttpServerRouter;
class QHttpServerRouterRule;
QT_END_NAMESPACE

// Type indices
enum : int {
    SBK_QAbstractHttpServer_IDX                              = 0,
    SBK_QFutureHttpServerResponse_IDX                        = 2,
    SBK_QFuture_QHttpServerResponse_IDX                      = 2,
    SBK_QHttpServer_IDX                                      = 3,
    SBK_QHttpServerConfiguration_IDX                         = 4,
    SBK_QHttpServerRequest_Method_IDX                        = 6,
    SBK_QFlags_QHttpServerRequest_Method_IDX                 = 1,
    SBK_QHttpServerRequest_IDX                               = 5,
    SBK_QHttpServerResponder_StatusCode_IDX                  = 8,
    SBK_QHttpServerResponder_IDX                             = 7,
    SBK_QHttpServerResponse_IDX                              = 9,
    SBK_QHttpServerRouter_IDX                                = 10,
    SBK_QHttpServerRouterRule_IDX                            = 11,
    SBK_QHttpServerWebSocketUpgradeResponse_ResponseType_IDX = 13,
    SBK_QHttpServerWebSocketUpgradeResponse_IDX              = 12,
    SBK_QtHttpServer_IDX_COUNT                               = 14,
};

// This variable stores all Python types exported by this module.
extern Shiboken::Module::TypeInitStruct *SbkPySide6_QtHttpServerTypeStructs;

// This variable stores the Python module object exported by this module.
extern PyObject *SbkPySide6_QtHttpServerModuleObject;

// This variable stores all type converters exported by this module.
extern SbkConverter **SbkPySide6_QtHttpServerTypeConverters;

// Converter indices
enum [[deprecated]] : int {
    SBK_QTHTTPSERVER_QLIST_INT_IDX                           = 0, // QList<int>
    SBK_QTHTTPSERVER_QHASH_QMETATYPE_QSTRING_IDX             = 1, // QHash<QMetaType,QString>
    SBK_QTHTTPSERVER_QLIST_QHTTPHEADERS_WELLKNOWNHEADER_IDX  = 2, // QList<QHttpHeaders::WellKnownHeader>
    SBK_QTHTTPSERVER_QLIST_QLOCALSERVERPTR_IDX               = 3, // QList<QLocalServer*>
    SBK_QTHTTPSERVER_QLIST_QUINT16_IDX                       = 4, // QList<quint16>
    SBK_QTHTTPSERVER_QLIST_QTCPSERVERPTR_IDX                 = 5, // QList<QTcpServer*>
    SBK_QTHTTPSERVER_QLIST_QVARIANT_IDX                      = 6, // QList<QVariant>
    SBK_QTHTTPSERVER_QLIST_QSTRING_IDX                       = 7, // QList<QString>
    SBK_QTHTTPSERVER_QMAP_QSTRING_QVARIANT_IDX               = 8, // QMap<QString,QVariant>
    SBK_QTHTTPSERVER_CONVERTERS_IDX_COUNT                    = 9,
};

// Converter indices
enum : int {
    SBK_QtHttpServer_QList_int_IDX                           = 0, // QList<int>
    SBK_QtHttpServer_QHash_QMetaType_QString_IDX             = 1, // QHash<QMetaType,QString>
    SBK_QtHttpServer_QList_QHttpHeaders_WellKnownHeader_IDX  = 2, // QList<QHttpHeaders::WellKnownHeader>
    SBK_QtHttpServer_QList_QLocalServerPTR_IDX               = 3, // QList<QLocalServer*>
    SBK_QtHttpServer_QList_quint16_IDX                       = 4, // QList<quint16>
    SBK_QtHttpServer_QList_QTcpServerPTR_IDX                 = 5, // QList<QTcpServer*>
    SBK_QtHttpServer_QList_QVariant_IDX                      = 6, // QList<QVariant>
    SBK_QtHttpServer_QList_QString_IDX                       = 7, // QList<QString>
    SBK_QtHttpServer_QMap_QString_QVariant_IDX               = 8, // QMap<QString,QVariant>
    SBK_QtHttpServer_CONVERTERS_IDX_COUNT                    = 9,
};

// typedef entries
using QFutureHttpServerResponse = QFuture<QHttpServerResponse>;

// Macros for type check

QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
namespace Shiboken
{

// PyType functions, to get the PyObjectType for a type T
template<> inline PyTypeObject *SbkType< ::QAbstractHttpServer >() { return Shiboken::Module::get(SbkPySide6_QtHttpServerTypeStructs[SBK_QAbstractHttpServer_IDX]); }
#if QT_CONFIG(future)
template<> inline PyTypeObject *SbkType< QFutureHttpServerResponse >() { return Shiboken::Module::get(SbkPySide6_QtHttpServerTypeStructs[SBK_QFutureHttpServerResponse_IDX]); }
#endif
template<> inline PyTypeObject *SbkType< ::QHttpServer >() { return Shiboken::Module::get(SbkPySide6_QtHttpServerTypeStructs[SBK_QHttpServer_IDX]); }
template<> inline PyTypeObject *SbkType< ::QHttpServerConfiguration >() { return Shiboken::Module::get(SbkPySide6_QtHttpServerTypeStructs[SBK_QHttpServerConfiguration_IDX]); }
template<> inline PyTypeObject *SbkType< ::QHttpServerRequest::Method >() { return Shiboken::Module::get(SbkPySide6_QtHttpServerTypeStructs[SBK_QHttpServerRequest_Method_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QHttpServerRequest::Method> >() { return Shiboken::Module::get(SbkPySide6_QtHttpServerTypeStructs[SBK_QFlags_QHttpServerRequest_Method_IDX]); }
template<> inline PyTypeObject *SbkType< ::QHttpServerRequest >() { return Shiboken::Module::get(SbkPySide6_QtHttpServerTypeStructs[SBK_QHttpServerRequest_IDX]); }
template<> inline PyTypeObject *SbkType< ::QHttpServerResponder::StatusCode >() { return Shiboken::Module::get(SbkPySide6_QtHttpServerTypeStructs[SBK_QHttpServerResponder_StatusCode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QHttpServerResponder >() { return Shiboken::Module::get(SbkPySide6_QtHttpServerTypeStructs[SBK_QHttpServerResponder_IDX]); }
template<> inline PyTypeObject *SbkType< ::QHttpServerResponse >() { return Shiboken::Module::get(SbkPySide6_QtHttpServerTypeStructs[SBK_QHttpServerResponse_IDX]); }
template<> inline PyTypeObject *SbkType< ::QHttpServerRouter >() { return Shiboken::Module::get(SbkPySide6_QtHttpServerTypeStructs[SBK_QHttpServerRouter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QHttpServerRouterRule >() { return Shiboken::Module::get(SbkPySide6_QtHttpServerTypeStructs[SBK_QHttpServerRouterRule_IDX]); }
template<> inline PyTypeObject *SbkType< ::QHttpServerWebSocketUpgradeResponse::ResponseType >() { return Shiboken::Module::get(SbkPySide6_QtHttpServerTypeStructs[SBK_QHttpServerWebSocketUpgradeResponse_ResponseType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QHttpServerWebSocketUpgradeResponse >() { return Shiboken::Module::get(SbkPySide6_QtHttpServerTypeStructs[SBK_QHttpServerWebSocketUpgradeResponse_IDX]); }

} // namespace Shiboken

QT_WARNING_POP
#endif // SBK_QTHTTPSERVER_PYTHON_H

