// Copyright (C) 2022 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only


#ifndef SBK_QTREMOTEOBJECTS_PYTHON_H
#define SBK_QTREMOTEOBJECTS_PYTHON_H

#include <sbkpython.h>
#include <sbkmodule.h>
#include <sbkconverter.h>
// Module Includes
#include <pyside6_qtcore_python.h>
#include <pyside6_qtnetwork_python.h>

// Bound library includes
#include <QtRemoteObjects/qremoteobjectnode.h>
#include <QtRemoteObjects/qremoteobjectpendingcall.h>
#include <QtRemoteObjects/qremoteobjectreplica.h>
#include <QtRemoteObjects/qtremoteobjectglobal.h>

QT_BEGIN_NAMESPACE
class QAbstractItemModelReplica;
class QConnectionAbstractServer;
class QRemoteObjectAbstractPersistedStore;
class QRemoteObjectDynamicReplica;
class QRemoteObjectHost;
class QRemoteObjectPendingCallWatcher;
class QRemoteObjectRegistry;
class QRemoteObjectRegistryHost;
class QRemoteObjectSettingsStore;
struct QRemoteObjectSourceLocationInfo;
class QtROClientFactory;
class QtROClientIoDevice;
class QtROIoDeviceBase;
class QtROServerFactory;
class QtROServerIoDevice;
QT_END_NAMESPACE

// Type indices
enum : int {
    SBK_QAbstractItemModelReplica_IDX                        = 0,
    SBK_QConnectionAbstractServer_IDX                        = 1,
    SBK_QRemoteObjectAbstractPersistedStore_IDX              = 2,
    SBK_QRemoteObjectDynamicReplica_IDX                      = 3,
    SBK_QRemoteObjectHost_IDX                                = 4,
    SBK_QRemoteObjectHostBase_AllowedSchemas_IDX             = 6,
    SBK_QRemoteObjectHostBase_IDX                            = 5,
    SBK_QRemoteObjectNode_ErrorCode_IDX                      = 8,
    SBK_QRemoteObjectNode_IDX                                = 7,
    SBK_QRemoteObjectPendingCall_Error_IDX                   = 10,
    SBK_QRemoteObjectPendingCall_IDX                         = 9,
    SBK_QRemoteObjectPendingCallWatcher_IDX                  = 11,
    SBK_QRemoteObjectRegistry_IDX                            = 12,
    SBK_QRemoteObjectRegistryHost_IDX                        = 13,
    SBK_QRemoteObjectReplica_State_IDX                       = 16,
    SBK_QRemoteObjectReplica_ConstructorType_IDX             = 15,
    SBK_QRemoteObjectReplica_IDX                             = 14,
    SBK_QRemoteObjectSettingsStore_IDX                       = 17,
    SBK_QRemoteObjectSourceLocationInfo_IDX                  = 18,
    SBK_QtROClientFactory_IDX                                = 19,
    SBK_QtROClientIoDevice_IDX                               = 20,
    SBK_QtROIoDeviceBase_IDX                                 = 21,
    SBK_QtROServerFactory_IDX                                = 22,
    SBK_QtROServerIoDevice_IDX                               = 23,
    SBK_QtRemoteObjects_QRemoteObjectPacketTypeEnum_IDX      = 26,
    SBK_QtRemoteObjects_InitialAction_IDX                    = 25,
    SBK_QtRemoteObjectsQtRemoteObjects_IDX                   = 24,
    SBK_QtRemoteObjects_IDX_COUNT                            = 27,
};

// This variable stores all Python types exported by this module.
extern Shiboken::Module::TypeInitStruct *SbkPySide6_QtRemoteObjectsTypeStructs;

// This variable stores the Python module object exported by this module.
extern PyObject *SbkPySide6_QtRemoteObjectsModuleObject;

// This variable stores all type converters exported by this module.
extern SbkConverter **SbkPySide6_QtRemoteObjectsTypeConverters;

// Converter indices
enum [[deprecated]] : int {
    SBK_QTREMOTEOBJECTS_QLIST_INT_IDX                        = 0, // QList<int>
    SBK_QTREMOTEOBJECTS_QSET_QSTRING_IDX                     = 1, // QSet<QString>
    SBK_QTREMOTEOBJECTS_QLIST_QVARIANT_IDX                   = 2, // QList<QVariant>
    SBK_QTREMOTEOBJECTS_STD_PAIR_QSTRING_QREMOTEOBJECTSOURCELOCATIONINFO_IDX = 3, // std::pair<QString,QRemoteObjectSourceLocationInfo>
    SBK_QTREMOTEOBJECTS_QHASH_QSTRING_QREMOTEOBJECTSOURCELOCATIONINFO_IDX = 4, // QHash<QString,QRemoteObjectSourceLocationInfo>
    SBK_QTREMOTEOBJECTS_QMAP_INT_QVARIANT_IDX                = 5, // QMap<int,QVariant>
    SBK_QTREMOTEOBJECTS_QLIST_QMODELINDEX_IDX                = 6, // QList<QModelIndex>
    SBK_QTREMOTEOBJECTS_QHASH_INT_QBYTEARRAY_IDX             = 7, // QHash<int,QByteArray>
    SBK_QTREMOTEOBJECTS_QLIST_QSTRING_IDX                    = 8, // QList<QString>
    SBK_QTREMOTEOBJECTS_QMAP_QSTRING_QVARIANT_IDX            = 9, // QMap<QString,QVariant>
    SBK_QTREMOTEOBJECTS_CONVERTERS_IDX_COUNT                 = 10,
};

// Converter indices
enum : int {
    SBK_QtRemoteObjects_QList_int_IDX                        = 0, // QList<int>
    SBK_QtRemoteObjects_QSet_QString_IDX                     = 1, // QSet<QString>
    SBK_QtRemoteObjects_QList_QVariant_IDX                   = 2, // QList<QVariant>
    SBK_QtRemoteObjects_std_pair_QString_QRemoteObjectSourceLocationInfo_IDX = 3, // std::pair<QString,QRemoteObjectSourceLocationInfo>
    SBK_QtRemoteObjects_QHash_QString_QRemoteObjectSourceLocationInfo_IDX = 4, // QHash<QString,QRemoteObjectSourceLocationInfo>
    SBK_QtRemoteObjects_QMap_int_QVariant_IDX                = 5, // QMap<int,QVariant>
    SBK_QtRemoteObjects_QList_QModelIndex_IDX                = 6, // QList<QModelIndex>
    SBK_QtRemoteObjects_QHash_int_QByteArray_IDX             = 7, // QHash<int,QByteArray>
    SBK_QtRemoteObjects_QList_QString_IDX                    = 8, // QList<QString>
    SBK_QtRemoteObjects_QMap_QString_QVariant_IDX            = 9, // QMap<QString,QVariant>
    SBK_QtRemoteObjects_CONVERTERS_IDX_COUNT                 = 10,
};
// Macros for type check

// Protected enum surrogates
enum PySide6_QtRemoteObjects_QRemoteObjectReplica_ConstructorType_Surrogate : int {};

QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
namespace Shiboken
{

// PyType functions, to get the PyObjectType for a type T
template<> inline PyTypeObject *SbkType< ::QAbstractItemModelReplica >() { return Shiboken::Module::get(SbkPySide6_QtRemoteObjectsTypeStructs[SBK_QAbstractItemModelReplica_IDX]); }
template<> inline PyTypeObject *SbkType< ::QConnectionAbstractServer >() { return Shiboken::Module::get(SbkPySide6_QtRemoteObjectsTypeStructs[SBK_QConnectionAbstractServer_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRemoteObjectAbstractPersistedStore >() { return Shiboken::Module::get(SbkPySide6_QtRemoteObjectsTypeStructs[SBK_QRemoteObjectAbstractPersistedStore_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRemoteObjectDynamicReplica >() { return Shiboken::Module::get(SbkPySide6_QtRemoteObjectsTypeStructs[SBK_QRemoteObjectDynamicReplica_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRemoteObjectHost >() { return Shiboken::Module::get(SbkPySide6_QtRemoteObjectsTypeStructs[SBK_QRemoteObjectHost_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRemoteObjectHostBase::AllowedSchemas >() { return Shiboken::Module::get(SbkPySide6_QtRemoteObjectsTypeStructs[SBK_QRemoteObjectHostBase_AllowedSchemas_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRemoteObjectHostBase >() { return Shiboken::Module::get(SbkPySide6_QtRemoteObjectsTypeStructs[SBK_QRemoteObjectHostBase_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRemoteObjectNode::ErrorCode >() { return Shiboken::Module::get(SbkPySide6_QtRemoteObjectsTypeStructs[SBK_QRemoteObjectNode_ErrorCode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRemoteObjectNode >() { return Shiboken::Module::get(SbkPySide6_QtRemoteObjectsTypeStructs[SBK_QRemoteObjectNode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRemoteObjectPendingCall::Error >() { return Shiboken::Module::get(SbkPySide6_QtRemoteObjectsTypeStructs[SBK_QRemoteObjectPendingCall_Error_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRemoteObjectPendingCall >() { return Shiboken::Module::get(SbkPySide6_QtRemoteObjectsTypeStructs[SBK_QRemoteObjectPendingCall_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRemoteObjectPendingCallWatcher >() { return Shiboken::Module::get(SbkPySide6_QtRemoteObjectsTypeStructs[SBK_QRemoteObjectPendingCallWatcher_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRemoteObjectRegistry >() { return Shiboken::Module::get(SbkPySide6_QtRemoteObjectsTypeStructs[SBK_QRemoteObjectRegistry_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRemoteObjectRegistryHost >() { return Shiboken::Module::get(SbkPySide6_QtRemoteObjectsTypeStructs[SBK_QRemoteObjectRegistryHost_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRemoteObjectReplica::State >() { return Shiboken::Module::get(SbkPySide6_QtRemoteObjectsTypeStructs[SBK_QRemoteObjectReplica_State_IDX]); }
template<> inline PyTypeObject *SbkType< ::PySide6_QtRemoteObjects_QRemoteObjectReplica_ConstructorType_Surrogate >() { return Shiboken::Module::get(SbkPySide6_QtRemoteObjectsTypeStructs[SBK_QRemoteObjectReplica_ConstructorType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRemoteObjectReplica >() { return Shiboken::Module::get(SbkPySide6_QtRemoteObjectsTypeStructs[SBK_QRemoteObjectReplica_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRemoteObjectSettingsStore >() { return Shiboken::Module::get(SbkPySide6_QtRemoteObjectsTypeStructs[SBK_QRemoteObjectSettingsStore_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRemoteObjectSourceLocationInfo >() { return Shiboken::Module::get(SbkPySide6_QtRemoteObjectsTypeStructs[SBK_QRemoteObjectSourceLocationInfo_IDX]); }
template<> inline PyTypeObject *SbkType< ::QtROClientFactory >() { return Shiboken::Module::get(SbkPySide6_QtRemoteObjectsTypeStructs[SBK_QtROClientFactory_IDX]); }
template<> inline PyTypeObject *SbkType< ::QtROClientIoDevice >() { return Shiboken::Module::get(SbkPySide6_QtRemoteObjectsTypeStructs[SBK_QtROClientIoDevice_IDX]); }
template<> inline PyTypeObject *SbkType< ::QtROIoDeviceBase >() { return Shiboken::Module::get(SbkPySide6_QtRemoteObjectsTypeStructs[SBK_QtROIoDeviceBase_IDX]); }
template<> inline PyTypeObject *SbkType< ::QtROServerFactory >() { return Shiboken::Module::get(SbkPySide6_QtRemoteObjectsTypeStructs[SBK_QtROServerFactory_IDX]); }
template<> inline PyTypeObject *SbkType< ::QtROServerIoDevice >() { return Shiboken::Module::get(SbkPySide6_QtRemoteObjectsTypeStructs[SBK_QtROServerIoDevice_IDX]); }
template<> inline PyTypeObject *SbkType< ::QtRemoteObjects::QRemoteObjectPacketTypeEnum >() { return Shiboken::Module::get(SbkPySide6_QtRemoteObjectsTypeStructs[SBK_QtRemoteObjects_QRemoteObjectPacketTypeEnum_IDX]); }
template<> inline PyTypeObject *SbkType< ::QtRemoteObjects::InitialAction >() { return Shiboken::Module::get(SbkPySide6_QtRemoteObjectsTypeStructs[SBK_QtRemoteObjects_InitialAction_IDX]); }

} // namespace Shiboken

QT_WARNING_POP
#endif // SBK_QTREMOTEOBJECTS_PYTHON_H

