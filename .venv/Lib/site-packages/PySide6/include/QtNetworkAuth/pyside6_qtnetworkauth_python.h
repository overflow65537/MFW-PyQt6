// Copyright (C) 2022 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only


#ifndef SBK_QTNETWORKAUTH_PYTHON_H
#define SBK_QTNETWORKAUTH_PYTHON_H

#include <sbkpython.h>
#include <sbkmodule.h>
#include <sbkconverter.h>
// Module Includes
#include <pyside6_qtnetwork_python.h>
#include <pyside6_qtcore_python.h>

// Bound library includes
#include <QtNetworkAuth/qabstractoauth.h>
#include <QtNetworkAuth/qabstractoauth2.h>
#include <QtNetworkAuth/qoauth1.h>
#include <QtNetworkAuth/qoauth1signature.h>
#include <QtNetworkAuth/qoauth2authorizationcodeflow.h>

QT_BEGIN_NAMESPACE
class QAbstractOAuthReplyHandler;
class QOAuth2DeviceAuthorizationFlow;
class QOAuthHttpServerReplyHandler;
class QOAuthOobReplyHandler;
class QOAuthUriSchemeReplyHandler;
QT_END_NAMESPACE

// Type indices
enum : int {
    SBK_QAbstractOAuth_Status_IDX                            = 6,
    SBK_QAbstractOAuth_Stage_IDX                             = 5,
    SBK_QAbstractOAuth_Error_IDX                             = 4,
    SBK_QAbstractOAuth_ContentType_IDX                       = 3,
    SBK_QAbstractOAuth_IDX                                   = 0,
    SBK_QAbstractOAuth2_NonceMode_IDX                        = 2,
    SBK_QAbstractOAuth2_IDX                                  = 1,
    SBK_QAbstractOAuthReplyHandler_IDX                       = 7,
    SBK_QOAuth1_SignatureMethod_IDX                          = 9,
    SBK_QOAuth1_IDX                                          = 8,
    SBK_QOAuth1Signature_HttpRequestMethod_IDX               = 11,
    SBK_QOAuth1Signature_IDX                                 = 10,
    SBK_QOAuth2AuthorizationCodeFlow_PkceMethod_IDX          = 13,
    SBK_QOAuth2AuthorizationCodeFlow_IDX                     = 12,
    SBK_QOAuth2DeviceAuthorizationFlow_IDX                   = 14,
    SBK_QOAuthHttpServerReplyHandler_IDX                     = 15,
    SBK_QOAuthOobReplyHandler_IDX                            = 16,
    SBK_QOAuthUriSchemeReplyHandler_IDX                      = 17,
    SBK_QtNetworkAuth_IDX_COUNT                              = 18,
};

// This variable stores all Python types exported by this module.
extern Shiboken::Module::TypeInitStruct *SbkPySide6_QtNetworkAuthTypeStructs;

// This variable stores the Python module object exported by this module.
extern PyObject *SbkPySide6_QtNetworkAuthModuleObject;

// This variable stores all type converters exported by this module.
extern SbkConverter **SbkPySide6_QtNetworkAuthTypeConverters;

// Converter indices
enum [[deprecated]] : int {
    SBK_QTNETWORKAUTH_QLIST_INT_IDX                          = 0, // QList<int>
    SBK_QTNETWORKAUTH_QMAP_QSTRING_QVARIANT_IDX              = 1, // QMap<QString,QVariant>
    SBK_QTNETWORKAUTH_QMULTIMAP_QSTRING_QVARIANT_IDX         = 2, // QMultiMap<QString,QVariant>
    SBK_QTNETWORKAUTH_STD_PAIR_QSTRING_QSTRING_IDX           = 3, // std::pair<QString,QString>
    SBK_QTNETWORKAUTH_QSET_QBYTEARRAY_IDX                    = 4, // QSet<QByteArray>
    SBK_QTNETWORKAUTH_QLIST_QSTRING_IDX                      = 5, // QList<QString>
    SBK_QTNETWORKAUTH_QLIST_QVARIANT_IDX                     = 6, // QList<QVariant>
    SBK_QTNETWORKAUTH_CONVERTERS_IDX_COUNT                   = 7,
};

// Converter indices
enum : int {
    SBK_QtNetworkAuth_QList_int_IDX                          = 0, // QList<int>
    SBK_QtNetworkAuth_QMap_QString_QVariant_IDX              = 1, // QMap<QString,QVariant>
    SBK_QtNetworkAuth_QMultiMap_QString_QVariant_IDX         = 2, // QMultiMap<QString,QVariant>
    SBK_QtNetworkAuth_std_pair_QString_QString_IDX           = 3, // std::pair<QString,QString>
    SBK_QtNetworkAuth_QSet_QByteArray_IDX                    = 4, // QSet<QByteArray>
    SBK_QtNetworkAuth_QList_QString_IDX                      = 5, // QList<QString>
    SBK_QtNetworkAuth_QList_QVariant_IDX                     = 6, // QList<QVariant>
    SBK_QtNetworkAuth_CONVERTERS_IDX_COUNT                   = 7,
};
// Macros for type check

QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
namespace Shiboken
{

// PyType functions, to get the PyObjectType for a type T
template<> inline PyTypeObject *SbkType< ::QAbstractOAuth::Status >() { return Shiboken::Module::get(SbkPySide6_QtNetworkAuthTypeStructs[SBK_QAbstractOAuth_Status_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractOAuth::Stage >() { return Shiboken::Module::get(SbkPySide6_QtNetworkAuthTypeStructs[SBK_QAbstractOAuth_Stage_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractOAuth::Error >() { return Shiboken::Module::get(SbkPySide6_QtNetworkAuthTypeStructs[SBK_QAbstractOAuth_Error_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractOAuth::ContentType >() { return Shiboken::Module::get(SbkPySide6_QtNetworkAuthTypeStructs[SBK_QAbstractOAuth_ContentType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractOAuth >() { return Shiboken::Module::get(SbkPySide6_QtNetworkAuthTypeStructs[SBK_QAbstractOAuth_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractOAuth2::NonceMode >() { return Shiboken::Module::get(SbkPySide6_QtNetworkAuthTypeStructs[SBK_QAbstractOAuth2_NonceMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractOAuth2 >() { return Shiboken::Module::get(SbkPySide6_QtNetworkAuthTypeStructs[SBK_QAbstractOAuth2_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractOAuthReplyHandler >() { return Shiboken::Module::get(SbkPySide6_QtNetworkAuthTypeStructs[SBK_QAbstractOAuthReplyHandler_IDX]); }
template<> inline PyTypeObject *SbkType< ::QOAuth1::SignatureMethod >() { return Shiboken::Module::get(SbkPySide6_QtNetworkAuthTypeStructs[SBK_QOAuth1_SignatureMethod_IDX]); }
template<> inline PyTypeObject *SbkType< ::QOAuth1 >() { return Shiboken::Module::get(SbkPySide6_QtNetworkAuthTypeStructs[SBK_QOAuth1_IDX]); }
template<> inline PyTypeObject *SbkType< ::QOAuth1Signature::HttpRequestMethod >() { return Shiboken::Module::get(SbkPySide6_QtNetworkAuthTypeStructs[SBK_QOAuth1Signature_HttpRequestMethod_IDX]); }
template<> inline PyTypeObject *SbkType< ::QOAuth1Signature >() { return Shiboken::Module::get(SbkPySide6_QtNetworkAuthTypeStructs[SBK_QOAuth1Signature_IDX]); }
template<> inline PyTypeObject *SbkType< ::QOAuth2AuthorizationCodeFlow::PkceMethod >() { return Shiboken::Module::get(SbkPySide6_QtNetworkAuthTypeStructs[SBK_QOAuth2AuthorizationCodeFlow_PkceMethod_IDX]); }
template<> inline PyTypeObject *SbkType< ::QOAuth2AuthorizationCodeFlow >() { return Shiboken::Module::get(SbkPySide6_QtNetworkAuthTypeStructs[SBK_QOAuth2AuthorizationCodeFlow_IDX]); }
template<> inline PyTypeObject *SbkType< ::QOAuth2DeviceAuthorizationFlow >() { return Shiboken::Module::get(SbkPySide6_QtNetworkAuthTypeStructs[SBK_QOAuth2DeviceAuthorizationFlow_IDX]); }
template<> inline PyTypeObject *SbkType< ::QOAuthHttpServerReplyHandler >() { return Shiboken::Module::get(SbkPySide6_QtNetworkAuthTypeStructs[SBK_QOAuthHttpServerReplyHandler_IDX]); }
template<> inline PyTypeObject *SbkType< ::QOAuthOobReplyHandler >() { return Shiboken::Module::get(SbkPySide6_QtNetworkAuthTypeStructs[SBK_QOAuthOobReplyHandler_IDX]); }
template<> inline PyTypeObject *SbkType< ::QOAuthUriSchemeReplyHandler >() { return Shiboken::Module::get(SbkPySide6_QtNetworkAuthTypeStructs[SBK_QOAuthUriSchemeReplyHandler_IDX]); }

} // namespace Shiboken

QT_WARNING_POP
#endif // SBK_QTNETWORKAUTH_PYTHON_H

