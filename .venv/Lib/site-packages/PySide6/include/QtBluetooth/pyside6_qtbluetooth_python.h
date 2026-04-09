// Copyright (C) 2022 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only


#ifndef SBK_QTBLUETOOTH_PYTHON_H
#define SBK_QTBLUETOOTH_PYTHON_H

#include <sbkpython.h>
#include <sbkmodule.h>
#include <sbkconverter.h>
// Module Includes
#include <pyside6_qtcore_python.h>

// Bound library includes
#include <QtBluetooth/qbluetooth.h>
#include <QtBluetooth/qbluetoothdevicediscoveryagent.h>
#include <QtBluetooth/qbluetoothdeviceinfo.h>
#include <QtBluetooth/qbluetoothlocaldevice.h>
#include <QtBluetooth/qbluetoothserver.h>
#include <QtBluetooth/qbluetoothservicediscoveryagent.h>
#include <QtBluetooth/qbluetoothserviceinfo.h>
#include <QtBluetooth/qbluetoothsocket.h>
#include <QtBluetooth/qbluetoothuuid.h>
#include <QtBluetooth/qlowenergyadvertisingdata.h>
#include <QtBluetooth/qlowenergyadvertisingparameters.h>
#include <QtBluetooth/qlowenergycharacteristic.h>
#include <QtBluetooth/qlowenergycontroller.h>
#include <QtBluetooth/qlowenergyservice.h>
#include <QtBluetooth/qlowenergyservicedata.h>

QT_BEGIN_NAMESPACE
class QBluetoothAddress;
class QBluetoothHostInfo;
class QLowEnergyCharacteristicData;
class QLowEnergyConnectionParameters;
class QLowEnergyDescriptor;
class QLowEnergyDescriptorData;
QT_END_NAMESPACE

// Type indices
enum : int {
    SBK_QBluetooth_Security_IDX                              = 2,
    SBK_QFlags_QBluetooth_Security_IDX                       = 46,
    SBK_QBluetooth_AttAccessConstraint_IDX                   = 1,
    SBK_QFlags_QBluetooth_AttAccessConstraint_IDX            = 45,
    SBK_QtBluetoothQBluetooth_IDX                            = 0,
    SBK_QBluetoothAddress_IDX                                = 3,
    SBK_QBluetoothDeviceDiscoveryAgent_Error_IDX             = 6,
    SBK_QBluetoothDeviceDiscoveryAgent_DiscoveryMethod_IDX   = 5,
    SBK_QFlags_QBluetoothDeviceDiscoveryAgent_DiscoveryMethod_IDX = 47,
    SBK_QBluetoothDeviceDiscoveryAgent_IDX                   = 4,
    SBK_QBluetoothDeviceInfo_MajorDeviceClass_IDX            = 10,
    SBK_QBluetoothDeviceInfo_MinorMiscellaneousClass_IDX     = 15,
    SBK_QBluetoothDeviceInfo_MinorComputerClass_IDX          = 12,
    SBK_QBluetoothDeviceInfo_MinorPhoneClass_IDX             = 18,
    SBK_QBluetoothDeviceInfo_MinorNetworkClass_IDX           = 16,
    SBK_QBluetoothDeviceInfo_MinorAudioVideoClass_IDX        = 11,
    SBK_QBluetoothDeviceInfo_MinorPeripheralClass_IDX        = 17,
    SBK_QBluetoothDeviceInfo_MinorImagingClass_IDX           = 14,
    SBK_QBluetoothDeviceInfo_MinorWearableClass_IDX          = 20,
    SBK_QBluetoothDeviceInfo_MinorToyClass_IDX               = 19,
    SBK_QBluetoothDeviceInfo_MinorHealthClass_IDX            = 13,
    SBK_QBluetoothDeviceInfo_ServiceClass_IDX                = 21,
    SBK_QFlags_QBluetoothDeviceInfo_ServiceClass_IDX         = 50,
    SBK_QBluetoothDeviceInfo_Field_IDX                       = 9,
    SBK_QFlags_QBluetoothDeviceInfo_Field_IDX                = 49,
    SBK_QBluetoothDeviceInfo_CoreConfiguration_IDX           = 8,
    SBK_QFlags_QBluetoothDeviceInfo_CoreConfiguration_IDX    = 48,
    SBK_QBluetoothDeviceInfo_IDX                             = 7,
    SBK_QBluetoothHostInfo_IDX                               = 22,
    SBK_QBluetoothLocalDevice_Pairing_IDX                    = 26,
    SBK_QBluetoothLocalDevice_HostMode_IDX                   = 25,
    SBK_QBluetoothLocalDevice_Error_IDX                      = 24,
    SBK_QBluetoothLocalDevice_IDX                            = 23,
    SBK_QBluetoothServer_Error_IDX                           = 28,
    SBK_QBluetoothServer_IDX                                 = 27,
    SBK_QBluetoothServiceDiscoveryAgent_Error_IDX            = 31,
    SBK_QBluetoothServiceDiscoveryAgent_DiscoveryMode_IDX    = 30,
    SBK_QBluetoothServiceDiscoveryAgent_IDX                  = 29,
    SBK_QBluetoothServiceInfo_AttributeId_IDX                = 34,
    SBK_QBluetoothServiceInfo_Protocol_IDX                   = 35,
    SBK_QBluetoothServiceInfo_IDX                            = 32,
    SBK_QBluetoothServiceInfo_Alternative_IDX                = 33,
    SBK_QBluetoothServiceInfo_Sequence_IDX                   = 36,
    SBK_QBluetoothSocket_SocketState_IDX                     = 39,
    SBK_QBluetoothSocket_SocketError_IDX                     = 38,
    SBK_QBluetoothSocket_IDX                                 = 37,
    SBK_QBluetoothUuid_ProtocolUuid_IDX                      = 43,
    SBK_QBluetoothUuid_ServiceClassUuid_IDX                  = 44,
    SBK_QBluetoothUuid_CharacteristicType_IDX                = 41,
    SBK_QBluetoothUuid_DescriptorType_IDX                    = 42,
    SBK_QBluetoothUuid_IDX                                   = 40,
    SBK_QLowEnergyAdvertisingData_Discoverability_IDX        = 54,
    SBK_QLowEnergyAdvertisingData_IDX                        = 53,
    SBK_QLowEnergyAdvertisingParameters_Mode_IDX             = 58,
    SBK_QLowEnergyAdvertisingParameters_FilterPolicy_IDX     = 57,
    SBK_QLowEnergyAdvertisingParameters_IDX                  = 55,
    SBK_QLowEnergyAdvertisingParameters_AddressInfo_IDX      = 56,
    SBK_QLowEnergyCharacteristic_PropertyType_IDX            = 60,
    SBK_QFlags_QLowEnergyCharacteristic_PropertyType_IDX     = 51,
    SBK_QLowEnergyCharacteristic_IDX                         = 59,
    SBK_QLowEnergyCharacteristicData_IDX                     = 61,
    SBK_QLowEnergyConnectionParameters_IDX                   = 62,
    SBK_QLowEnergyController_Error_IDX                       = 65,
    SBK_QLowEnergyController_ControllerState_IDX             = 64,
    SBK_QLowEnergyController_RemoteAddressType_IDX           = 66,
    SBK_QLowEnergyController_Role_IDX                        = 67,
    SBK_QLowEnergyController_IDX                             = 63,
    SBK_QLowEnergyDescriptor_IDX                             = 68,
    SBK_QLowEnergyDescriptorData_IDX                         = 69,
    SBK_QLowEnergyService_ServiceType_IDX                    = 74,
    SBK_QFlags_QLowEnergyService_ServiceType_IDX             = 52,
    SBK_QLowEnergyService_ServiceError_IDX                   = 72,
    SBK_QLowEnergyService_ServiceState_IDX                   = 73,
    SBK_QLowEnergyService_DiscoveryMode_IDX                  = 71,
    SBK_QLowEnergyService_WriteMode_IDX                      = 75,
    SBK_QLowEnergyService_IDX                                = 70,
    SBK_QLowEnergyServiceData_ServiceType_IDX                = 77,
    SBK_QLowEnergyServiceData_IDX                            = 76,
    SBK_QtBluetooth_IDX_COUNT                                = 78,
};

// This variable stores all Python types exported by this module.
extern Shiboken::Module::TypeInitStruct *SbkPySide6_QtBluetoothTypeStructs;

// This variable stores the Python module object exported by this module.
extern PyObject *SbkPySide6_QtBluetoothModuleObject;

// This variable stores all type converters exported by this module.
extern SbkConverter **SbkPySide6_QtBluetoothTypeConverters;

// Converter indices
enum [[deprecated]] : int {
    SBK_QTBLUETOOTH_QLIST_INT_IDX                            = 0, // QList<int>
    SBK_QTBLUETOOTH_QLIST_QLOWENERGYCHARACTERISTICDATA_IDX   = 1, // QList<QLowEnergyCharacteristicData>
    SBK_QTBLUETOOTH_QLIST_QLOWENERGYSERVICEPTR_IDX           = 2, // QList<QLowEnergyService*>
    SBK_QTBLUETOOTH_QLIST_QLOWENERGYCHARACTERISTIC_IDX       = 3, // QList<QLowEnergyCharacteristic>
    SBK_QTBLUETOOTH_QLIST_QBLUETOOTHUUID_IDX                 = 4, // QList<QBluetoothUuid>
    SBK_QTBLUETOOTH_QLIST_QLOWENERGYDESCRIPTORDATA_IDX       = 5, // QList<QLowEnergyDescriptorData>
    SBK_QTBLUETOOTH_QLIST_QLOWENERGYDESCRIPTOR_IDX           = 6, // QList<QLowEnergyDescriptor>
    SBK_QTBLUETOOTH_QLIST_QLOWENERGYADVERTISINGPARAMETERS_ADDRESSINFO_IDX = 7, // QList<QLowEnergyAdvertisingParameters::AddressInfo>
    SBK_QTBLUETOOTH_QLIST_QBLUETOOTHSERVICEINFO_IDX          = 8, // QList<QBluetoothServiceInfo>
    SBK_QTBLUETOOTH_QLIST_QBLUETOOTHHOSTINFO_IDX             = 9, // QList<QBluetoothHostInfo>
    SBK_QTBLUETOOTH_QLIST_QBLUETOOTHADDRESS_IDX              = 10, // QList<QBluetoothAddress>
    SBK_QTBLUETOOTH_QMULTIHASH_QUINT16_QBYTEARRAY_IDX        = 11, // QMultiHash<quint16,QByteArray>
    SBK_QTBLUETOOTH_QLIST_QUINT16_IDX                        = 12, // QList<quint16>
    SBK_QTBLUETOOTH_QMULTIHASH_QBLUETOOTHUUID_QBYTEARRAY_IDX = 13, // QMultiHash<QBluetoothUuid,QByteArray>
    SBK_QTBLUETOOTH_QLIST_QBLUETOOTHDEVICEINFO_IDX           = 14, // QList<QBluetoothDeviceInfo>
    SBK_QTBLUETOOTH_QLIST_QVARIANT_IDX                       = 15, // QList<QVariant>
    SBK_QTBLUETOOTH_QLIST_QSTRING_IDX                        = 16, // QList<QString>
    SBK_QTBLUETOOTH_QMAP_QSTRING_QVARIANT_IDX                = 17, // QMap<QString,QVariant>
    SBK_QTBLUETOOTH_CONVERTERS_IDX_COUNT                     = 18,
};

// Converter indices
enum : int {
    SBK_QtBluetooth_QList_int_IDX                            = 0, // QList<int>
    SBK_QtBluetooth_QList_QLowEnergyCharacteristicData_IDX   = 1, // QList<QLowEnergyCharacteristicData>
    SBK_QtBluetooth_QList_QLowEnergyServicePTR_IDX           = 2, // QList<QLowEnergyService*>
    SBK_QtBluetooth_QList_QLowEnergyCharacteristic_IDX       = 3, // QList<QLowEnergyCharacteristic>
    SBK_QtBluetooth_QList_QBluetoothUuid_IDX                 = 4, // QList<QBluetoothUuid>
    SBK_QtBluetooth_QList_QLowEnergyDescriptorData_IDX       = 5, // QList<QLowEnergyDescriptorData>
    SBK_QtBluetooth_QList_QLowEnergyDescriptor_IDX           = 6, // QList<QLowEnergyDescriptor>
    SBK_QtBluetooth_QList_QLowEnergyAdvertisingParameters_AddressInfo_IDX = 7, // QList<QLowEnergyAdvertisingParameters::AddressInfo>
    SBK_QtBluetooth_QList_QBluetoothServiceInfo_IDX          = 8, // QList<QBluetoothServiceInfo>
    SBK_QtBluetooth_QList_QBluetoothHostInfo_IDX             = 9, // QList<QBluetoothHostInfo>
    SBK_QtBluetooth_QList_QBluetoothAddress_IDX              = 10, // QList<QBluetoothAddress>
    SBK_QtBluetooth_QMultiHash_quint16_QByteArray_IDX        = 11, // QMultiHash<quint16,QByteArray>
    SBK_QtBluetooth_QList_quint16_IDX                        = 12, // QList<quint16>
    SBK_QtBluetooth_QMultiHash_QBluetoothUuid_QByteArray_IDX = 13, // QMultiHash<QBluetoothUuid,QByteArray>
    SBK_QtBluetooth_QList_QBluetoothDeviceInfo_IDX           = 14, // QList<QBluetoothDeviceInfo>
    SBK_QtBluetooth_QList_QVariant_IDX                       = 15, // QList<QVariant>
    SBK_QtBluetooth_QList_QString_IDX                        = 16, // QList<QString>
    SBK_QtBluetooth_QMap_QString_QVariant_IDX                = 17, // QMap<QString,QVariant>
    SBK_QtBluetooth_CONVERTERS_IDX_COUNT                     = 18,
};
// Macros for type check

QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
namespace Shiboken
{

// PyType functions, to get the PyObjectType for a type T
template<> inline PyTypeObject *SbkType< ::QBluetooth::Security >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetooth_Security_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QBluetooth::Security> >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QFlags_QBluetooth_Security_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetooth::AttAccessConstraint >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetooth_AttAccessConstraint_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QBluetooth::AttAccessConstraint> >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QFlags_QBluetooth_AttAccessConstraint_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothAddress >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothAddress_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothDeviceDiscoveryAgent::Error >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothDeviceDiscoveryAgent_Error_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothDeviceDiscoveryAgent::DiscoveryMethod >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothDeviceDiscoveryAgent_DiscoveryMethod_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QBluetoothDeviceDiscoveryAgent::DiscoveryMethod> >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QFlags_QBluetoothDeviceDiscoveryAgent_DiscoveryMethod_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothDeviceDiscoveryAgent >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothDeviceDiscoveryAgent_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothDeviceInfo::MajorDeviceClass >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothDeviceInfo_MajorDeviceClass_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothDeviceInfo::MinorMiscellaneousClass >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothDeviceInfo_MinorMiscellaneousClass_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothDeviceInfo::MinorComputerClass >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothDeviceInfo_MinorComputerClass_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothDeviceInfo::MinorPhoneClass >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothDeviceInfo_MinorPhoneClass_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothDeviceInfo::MinorNetworkClass >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothDeviceInfo_MinorNetworkClass_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothDeviceInfo::MinorAudioVideoClass >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothDeviceInfo_MinorAudioVideoClass_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothDeviceInfo::MinorPeripheralClass >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothDeviceInfo_MinorPeripheralClass_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothDeviceInfo::MinorImagingClass >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothDeviceInfo_MinorImagingClass_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothDeviceInfo::MinorWearableClass >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothDeviceInfo_MinorWearableClass_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothDeviceInfo::MinorToyClass >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothDeviceInfo_MinorToyClass_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothDeviceInfo::MinorHealthClass >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothDeviceInfo_MinorHealthClass_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothDeviceInfo::ServiceClass >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothDeviceInfo_ServiceClass_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QBluetoothDeviceInfo::ServiceClass> >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QFlags_QBluetoothDeviceInfo_ServiceClass_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothDeviceInfo::Field >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothDeviceInfo_Field_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QBluetoothDeviceInfo::Field> >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QFlags_QBluetoothDeviceInfo_Field_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothDeviceInfo::CoreConfiguration >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothDeviceInfo_CoreConfiguration_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QBluetoothDeviceInfo::CoreConfiguration> >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QFlags_QBluetoothDeviceInfo_CoreConfiguration_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothDeviceInfo >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothDeviceInfo_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothHostInfo >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothHostInfo_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothLocalDevice::Pairing >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothLocalDevice_Pairing_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothLocalDevice::HostMode >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothLocalDevice_HostMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothLocalDevice::Error >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothLocalDevice_Error_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothLocalDevice >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothLocalDevice_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothServer::Error >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothServer_Error_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothServer >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothServer_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothServiceDiscoveryAgent::Error >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothServiceDiscoveryAgent_Error_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothServiceDiscoveryAgent::DiscoveryMode >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothServiceDiscoveryAgent_DiscoveryMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothServiceDiscoveryAgent >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothServiceDiscoveryAgent_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothServiceInfo::AttributeId >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothServiceInfo_AttributeId_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothServiceInfo::Protocol >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothServiceInfo_Protocol_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothServiceInfo >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothServiceInfo_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothServiceInfo::Alternative >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothServiceInfo_Alternative_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothServiceInfo::Sequence >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothServiceInfo_Sequence_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothSocket::SocketState >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothSocket_SocketState_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothSocket::SocketError >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothSocket_SocketError_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothSocket >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothSocket_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothUuid::ProtocolUuid >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothUuid_ProtocolUuid_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothUuid::ServiceClassUuid >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothUuid_ServiceClassUuid_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothUuid::CharacteristicType >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothUuid_CharacteristicType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothUuid::DescriptorType >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothUuid_DescriptorType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothUuid >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QBluetoothUuid_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLowEnergyAdvertisingData::Discoverability >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QLowEnergyAdvertisingData_Discoverability_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLowEnergyAdvertisingData >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QLowEnergyAdvertisingData_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLowEnergyAdvertisingParameters::Mode >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QLowEnergyAdvertisingParameters_Mode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLowEnergyAdvertisingParameters::FilterPolicy >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QLowEnergyAdvertisingParameters_FilterPolicy_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLowEnergyAdvertisingParameters >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QLowEnergyAdvertisingParameters_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLowEnergyAdvertisingParameters::AddressInfo >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QLowEnergyAdvertisingParameters_AddressInfo_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLowEnergyCharacteristic::PropertyType >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QLowEnergyCharacteristic_PropertyType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QLowEnergyCharacteristic::PropertyType> >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QFlags_QLowEnergyCharacteristic_PropertyType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLowEnergyCharacteristic >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QLowEnergyCharacteristic_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLowEnergyCharacteristicData >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QLowEnergyCharacteristicData_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLowEnergyConnectionParameters >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QLowEnergyConnectionParameters_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLowEnergyController::Error >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QLowEnergyController_Error_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLowEnergyController::ControllerState >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QLowEnergyController_ControllerState_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLowEnergyController::RemoteAddressType >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QLowEnergyController_RemoteAddressType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLowEnergyController::Role >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QLowEnergyController_Role_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLowEnergyController >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QLowEnergyController_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLowEnergyDescriptor >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QLowEnergyDescriptor_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLowEnergyDescriptorData >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QLowEnergyDescriptorData_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLowEnergyService::ServiceType >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QLowEnergyService_ServiceType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QLowEnergyService::ServiceType> >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QFlags_QLowEnergyService_ServiceType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLowEnergyService::ServiceError >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QLowEnergyService_ServiceError_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLowEnergyService::ServiceState >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QLowEnergyService_ServiceState_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLowEnergyService::DiscoveryMode >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QLowEnergyService_DiscoveryMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLowEnergyService::WriteMode >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QLowEnergyService_WriteMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLowEnergyService >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QLowEnergyService_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLowEnergyServiceData::ServiceType >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QLowEnergyServiceData_ServiceType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLowEnergyServiceData >() { return Shiboken::Module::get(SbkPySide6_QtBluetoothTypeStructs[SBK_QLowEnergyServiceData_IDX]); }

} // namespace Shiboken

QT_WARNING_POP
#endif // SBK_QTBLUETOOTH_PYTHON_H

